from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (AdminUserViewSet, CategoryViewSet, CommentView,
                    GenreViewSet, ReviewView, TitleViewSet, get_jwt_token,
                    send_confirmation_code)

app_name = 'api'
router_v1 = DefaultRouter()

router_v1.register('users', AdminUserViewSet, basename='users')
router_v1.register('titles', TitleViewSet, basename='titles')
router_v1.register('genres', GenreViewSet, basename='genres')
router_v1.register('categories', CategoryViewSet, basename='categories')
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews', ReviewView, basename='reviews'
)
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentView,
    basename='comments'
)


urlpatterns = [
    path('v1/', include(router_v1.urls)),
    path('v1/auth/signup/', send_confirmation_code),
    path('v1/auth/token/', get_jwt_token)
]
