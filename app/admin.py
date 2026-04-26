from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from app.database import engine
from app.models import User, Post, Comment, Tag
from app.config import ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_SECRET_KEY

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            request.session.update({"admin_authenticated": True})
            return True
        return False
    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True
    async def authenticate(self, request: Request) -> bool:
        return request.session.get("admin_authenticated", False)

class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    column_list = [
        User.id,
        User.username,
        User.nickname,
        User.bio,
        User.is_private,
        User.created_at,
        User.avatar_path,
        User.header_path
    ]
    column_searchable_list = [User.username, User.nickname]
    column_sortable_list = [User.id, User.created_at]
    can_create = False
    can_edit = True
    can_delete = True
    can_view_details = True
    column_labels = {
        User.id: "ID",
        User.username: "Логин",
        User.nickname: "Имя",
        User.bio: "О себе",
        User.is_private: "Приватный",
        User.created_at: "Создан",
        User.avatar_path: "Аватар",
        User.header_path: "Шапка"
    }
class PostAdmin(ModelView, model=Post):
    name = "Пост"
    name_plural = "Посты"
    column_list = [
        Post.id,
        Post.description,
        Post.user_id,
        Post.created_at,
        Post.image_path
    ]
    column_searchable_list = [Post.description]
    column_sortable_list = [Post.id, Post.created_at]
    can_delete = True
    column_labels = {
        Post.id: "ID",
        Post.description: "Описание",
        Post.user_id: "ID автора",
        Post.created_at: "Создан",
        Post.image_path: "Картинка"
    }
class TagAdmin(ModelView, model=Tag):
    name = "Тег"
    name_plural = "Теги"
    column_list = [Tag.id, Tag.name, Tag.created_at]
    column_searchable_list = [Tag.name]
    can_delete = True
class CommentAdmin(ModelView, model=Comment):
    name = "Комментарий"
    name_plural = "Комментарии"
    column_list = [
        Comment.id,
        Comment.text,
        Comment.user_id,
        Comment.post_id,
        Comment.created_at
    ]
    column_searchable_list = [Comment.text]
    can_delete = True
    column_labels = {
        Comment.id: "ID",
        Comment.text: "Текст",
        Comment.user_id: "ID автора",
        Comment.post_id: "ID поста",
        Comment.created_at: "Создан"
    }




def setup_admin(app):
    authentication_backend = AdminAuth(secret_key=ADMIN_SECRET_KEY)
    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=authentication_backend,
        title="Нить | некая админка",
        base_url="/admin"
    )
    admin.add_view(UserAdmin)
    admin.add_view(PostAdmin)
    admin.add_view(CommentAdmin)
    admin.add_view(TagAdmin)
    return admin