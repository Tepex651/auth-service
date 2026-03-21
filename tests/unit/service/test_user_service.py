from uuid import uuid4
from sqlalchemy.exc import IntegrityError
from pydantic import SecretStr
import pytest
from app.constants import Roles
from app.db.models.role import Role
from app.db.models.user import User
from app.exceptions.auth import AccountDisabled, InvalidCredentials
from app.exceptions.user import InvalidCurrentPassword, RoleNotFound, UserAlreadyExists, UserException, UserNotFound
from app.repository.role import RoleRepository
from app.repository.user import UserRepository
from app.security.hasher import SecureHasher
from app.service.user_service import UserService


@pytest.fixture
def user_repository(mocker):
    return mocker.AsyncMock(spec=UserRepository)


@pytest.fixture
def role_repository(mocker):
    return mocker.AsyncMock(spec=RoleRepository)


@pytest.fixture
def hasher(mocker):
    return mocker.Mock(spec=SecureHasher)


@pytest.fixture
def user_service(user_repository, role_repository, hasher) -> UserService:
    return UserService(
        user_repository=user_repository,
        role_repository=role_repository,
        hasher=hasher,
    )


################################# TEST AUTHENTICATE #################################
async def test_authenticate_success(
    user_service: UserService,
    user_repository,
    hasher,
):
    username = "testuser"
    password = "testpassword"
    hashed_password = "hashed_testpassword"

    user = User(
        id=uuid4(),
        username=username,
        email="test_email@test.com",
        hashed_password=hashed_password,
        active=True,
        email_confirmed=True,
    )
    hasher.verify.return_value = True
    user_repository.get_by_username.return_value = user

    authenticated_user = await user_service.authenticate(username=username, password=SecretStr(password))

    assert authenticated_user == user


async def test_authenticate_invalid_username(
    user_service: UserService,
    user_repository,
):
    user_repository.get_by_username.return_value = None

    with pytest.raises(InvalidCredentials):
        await user_service.authenticate(username="invaliduser", password=SecretStr("somepassword"))


async def test_authenticate_invalid_password(
    user_service: UserService,
    user_repository,
    hasher,
):
    username = "testuser"
    wrong_password = "wrongpassword"
    hashed_password = "hashed_correctpassword"

    user = User(
        id=uuid4(),
        username=username,
        email="test@test.com",
        hashed_password=hashed_password,
        active=True,
    )
    hasher.verify.side_effect = lambda secret, hashed: secret == hashed_password and hashed == hashed_password
    user_repository.get_by_username.return_value = user

    with pytest.raises(InvalidCredentials):
        await user_service.authenticate(username=username, password=SecretStr(wrong_password))


async def test_authenticate_inactive_account(
    user_service: UserService,
    user_repository,
    hasher,
):
    username = "testuser"
    password = "testpassword"
    hashed_password = "hashed_testpassword"

    user = User(
        id=uuid4(),
        username=username,
        email="test@test.com",
        hashed_password=hashed_password,
        active=False,
    )
    hasher.verify.return_value = True
    user_repository.get_by_username.return_value = user
    with pytest.raises(AccountDisabled):
        await user_service.authenticate(username=username, password=SecretStr(password))


################################# TEST CREATE USER #################################
async def test_create_user_success(
    user_service: UserService,
    user_repository,
    role_repository,
    hasher,
):
    username = "newuser"
    password = "newpassword"
    email = "test@test.com"
    role_name = Roles.USER.value
    role = Role(
        id=1,
        name=role_name,
    )
    user_id = uuid4()
    new_user = User(
        id=user_id,
        username=username,
        email=email,
        active=True,
        role_id=role.id,
    )

    role_repository.get_by_name.return_value = role
    user_repository.insert.return_value = new_user
    hasher.hash.side_effect = lambda pwd: f"hashed_{pwd}"
    created_user = await user_service.create_user(
        username=username,
        password=SecretStr(password),
        email=email,
        role_name=role_name,
    )

    assert created_user == new_user


async def test_create_user_raises_if_role_not_exists(
    user_service: UserService,
    role_repository,
):
    role_repository.get_by_name.return_value = None

    with pytest.raises(RoleNotFound):
        await user_service.create_user(
            username="newuser",
            password=SecretStr("newpassword"),
            email="test@test.com",
            role_name=Roles.USER.value,
        )


async def test_create_user_raises_if_creation_failed(
    user_service: UserService,
    user_repository,
    role_repository,
):
    role = Role(
        id=1,
        name=Roles.USER.value,
    )

    role_repository.get_by_name.return_value = role
    user_repository.insert.side_effect = IntegrityError(
        "duplicate key value violates unique constraint",
        params=None,
        orig=UserAlreadyExists(),
    )

    with pytest.raises(UserAlreadyExists):
        await user_service.create_user(
            username="newuser",
            password=SecretStr("newpassword"),
            email="test@test.com",
            role_name=Roles.USER.value,
        )


################################# TEST GET USER #################################
async def test_get_user(
    user_service: UserService,
    user_repository,
):
    user_id = uuid4()
    user = User(
        id=user_id,
        email="test@test.com",
        username="test",
        active=True,
    )

    user_repository.get_by_id.return_value = user

    result = await user_service.get_user(user_id)

    assert result is user

    user_repository.get_by_id.assert_awaited_once_with(
        user_id=user_id,
    )


async def test_get_user_not_found(
    user_service: UserService,
    user_repository,
):
    user_repository.get_by_id.return_value = None

    with pytest.raises(UserNotFound):
        await user_service.get_user(uuid4())


################################# TEST GET USER BY EMAIL #################################
async def test_get_user_by_email(
    user_service: UserService,
    user_repository,
):
    user = User(
        id=uuid4(),
        email="test@test.com",
        username="test",
        active=True,
    )

    user_repository.get_by_email.return_value = user

    result = await user_service.get_user_by_email(email=user.email)

    assert result is user

    user_repository.get_by_email.assert_awaited_once_with(
        email=user.email,
    )


async def test_get_user_by_email_not_found(
    user_service: UserService,
    user_repository,
):
    user_repository.get_by_email.return_value = None
    with pytest.raises(UserNotFound):
        await user_service.get_user_by_email(email="nonexistent@test.com")


################################# TEST ASSIGN ROLE #################################
async def test_assign_role_success(
    user_service: UserService,
    user_repository,
    role_repository,
):
    user_id = uuid4()

    role = Role(
        id=1,
        name="admin",
    )

    updated_user = User(
        id=user_id,
        email="test@test.com",
        username="test",
        active=True,
        role_id=role.id,
    )

    role_repository.get_by_name.return_value = role
    user_repository.update_role.return_value = updated_user

    await user_service.assign_role(
        user_id=user_id,
        role_name=Roles.ADMIN,
    )

    role_repository.get_by_name.assert_awaited_once_with(
        name=Roles.ADMIN.value,
    )

    user_repository.update_role.assert_awaited_once_with(
        user_id=user_id,
        role_id=role.id,
    )


async def test_assign_role_raises_if_role_not_exists(
    user_service: UserService,
    user_repository,
    role_repository,
):
    role_repository.get_by_name.return_value = None

    with pytest.raises(RoleNotFound):
        await user_service.assign_role(
            user_id=uuid4(),
            role_name=Roles.ADMIN,
        )

    role_repository.get_by_name.assert_awaited_once()
    user_repository.update_role.assert_not_called()


async def test_assign_role_raises_if_update_failed(
    user_service,
    role_repository,
    user_repository,
):
    role = Role(id=uuid4(), name="admin")
    role_repository.get_by_name.return_value = role
    user_repository.update_role.return_value = False

    with pytest.raises(UserNotFound):
        await user_service.assign_role(uuid4(), Roles.ADMIN)


################################# TEST SET ACTIVE #################################
async def test_set_active_delegates_to_repository(
    user_service: UserService,
    user_repository,
):
    user_id = uuid4()
    updated_user = User(
        id=user_id,
        email="test@test.com",
        username="test",
        active=False,
    )

    user_repository.update_active.return_value = updated_user

    await user_service.set_active(
        user_id=user_id,
        active=False,
    )

    user_repository.update_active.assert_awaited_once_with(
        user_id=user_id,
        active=False,
    )


async def test_set_active_raises_if_update_failed(
    user_service: UserService,
    user_repository,
):
    user_repository.update_active.return_value = None

    with pytest.raises(UserNotFound):
        await user_service.set_active(
            user_id=uuid4(),
            active=True,
        )


################################# TEST UPDATE LAST LOGIN #################################
async def test_update_last_login_success(
    user_service: UserService,
    user_repository,
):
    user_repository.update_last_login.return_value = True

    await user_service.update_last_login_now(user_id=uuid4())

    user_repository.update_last_login.assert_awaited_once()


async def test_update_last_login_raises_if_update_failed(
    user_service: UserService,
    user_repository,
):
    user_repository.update_last_login.return_value = False
    with pytest.raises(UserNotFound):
        await user_service.update_last_login_now(
            user_id=uuid4(),
        )


################################# TEST UPDATE MFA STATE #################################
async def test_update_mfa_state_success(
    user_service: UserService,
    user_repository,
):
    user_repository.update_mfa_state.return_value = True

    await user_service.update_mfa_state(user_id=uuid4(), mfa_enabled=True)

    user_repository.update_mfa_state.assert_awaited_once()


async def test_update_mfa_state_raises_if_update_failed(
    user_service: UserService,
    user_repository,
):
    user_repository.update_mfa_state.return_value = False
    with pytest.raises(UserNotFound):
        await user_service.update_mfa_state(
            user_id=uuid4(),
            mfa_enabled=True,
        )


################################# TEST SET PASSWORD #################################
async def test_update_password_success(
    user_service: UserService,
    user_repository,
):
    user_repository.update_password.return_value = True

    await user_service.set_password(user_id=uuid4(), new_password=SecretStr("new_password"))

    user_repository.update_password.assert_awaited_once()


async def test_update_password_raises_if_update_failed(
    user_service: UserService,
    user_repository,
):
    user_repository.update_password.return_value = False
    with pytest.raises(UserNotFound):
        await user_service.set_password(
            user_id=uuid4(),
            new_password=SecretStr("new_password"),
        )


################################# TEST CHANGE PASSWORD #################################
async def test_change_password_success(
    user_service: UserService,
    user_repository,
    hasher,
):
    user_id = uuid4()
    user_repository.get_by_id.return_value = User(
        id=user_id,
        email="test@test.com",
        username="test",
        active=True,
    )
    hasher.verify.return_value = True

    await user_service.change_password(
        user_id=user_id,
        old_password=SecretStr("old_password"),
        new_password=SecretStr("new_password"),
    )

    user_repository.update_password.return_value = True


async def test_change_password_raises_if_invalid_current_password(
    user_service: UserService,
    user_repository,
    hasher,
):
    user_id = uuid4()
    user_repository.get_by_id.return_value = User(
        id=user_id,
        email="test@test.com",
        username="test",
        active=True,
    )
    hasher.verify.return_value = False

    with pytest.raises(InvalidCurrentPassword):
        await user_service.change_password(
            user_id=user_id,
            old_password=SecretStr("old_password"),
            new_password=SecretStr("new_password"),
        )
    user_repository.update_password.return_value = False
