from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from reviews.models import Category, Genre, Review, Title

from .filters import TitleFilter
from .permissions import (IsAdminRole, IsMe, IsReadOnly,
                          RetrieveOnlyOrHasCUDPermissions)
from .serializers import (AdminUserSerializer, CategorySerializer,
                          CommentSerializer, ConfirmationCodeSerializer,
                          GenreSerializer, JWTTokenSerializer, MeSerializer,
                          ReviewSerializer, TitlePostSerializer,
                          TitleViewSerializer)

User = get_user_model()


def send_code(user):
    '''
    Function that is responsible for
    generating confirmation code for a user
    and sending email with the code to them.
    '''
    confirmation_code = default_token_generator.make_token(user)
    send_mail(
        'Код подтверждения',
        f'Ваш код подтверждения: {confirmation_code}',
        settings.DEFAULT_FROM_EMAIL,
        (user.email,),
        fail_silently=False,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def send_confirmation_code(request):
    '''
    View function responsible for signup of new users.
    '''
    serializer = ConfirmationCodeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data.get('username')
    email = serializer.validated_data.get('email')
    try:
        user, created = User.objects.get_or_create(
            username=username,
            email=email
        )
    except Exception:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    send_code(user)
    if created:
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def get_jwt_token(request):
    '''
    Responsible for generating jwt tokens.
    In case of successful request it returns user's jwt token to access API.
    '''
    serializer = JWTTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data.get('username')
    confirmation_code = serializer.validated_data.get('confirmation_code')
    user = get_object_or_404(
        User, username=username
    )
    if default_token_generator.check_token(user, confirmation_code):
        token = AccessToken.for_user(user).access_token()
        resp = {'token': token}
        return Response(resp, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminUserViewSet(viewsets.ModelViewSet):
    '''
    ViewSet to handle requests to the '.../api/v1/users/' endpoint.
    Permission to interact with the ViewSet is entrusted only to
    users with admin role.
    Endpoint '.../users/me/' is accessible only to an owner of an account.
    '''
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = (IsAdminRole,)
    filter_backends = (SearchFilter,)
    search_fields = ('username',)
    pagination_class = LimitOffsetPagination
    lookup_field = 'username'

    @action(
        methods=['GET', 'PATCH'],
        detail=False,
        url_path='me',
        url_name='me',
        permission_classes=(IsMe,)
    )
    def me(self, request):
        user = get_object_or_404(User, username=request.user.username)
        if request.method == 'PATCH':
            serializer = MeSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = MeSerializer(user, partial=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateListViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    '''
    Base ViewSet that supports only requests
    to create, destroy or return a list of objects.
    '''
    permission_classes = [IsReadOnly | IsAdminRole]
    filter_backends = [SearchFilter]
    search_fields = ['name']
    lookup_field = 'slug'


class CategoryViewSet(CreateListViewSet):
    '''
    ViewSet to handle requests to the '.../api/v1/categories/' endpoint.
    Inherits from CreateListViewSet.
    '''
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(CreateListViewSet):
    '''
    ViewSet to handle requests to the '.../api/v1/genres/' endpoint.
    Inherits from CreateListViewSet.
    '''
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleViewSet(viewsets.ModelViewSet):
    '''
    ViewSet to handle requests to the '.../api/v1/titles/' endpoint.
    '''
    queryset = Title.objects.annotate(rating=Avg('reviews__score'))
    permission_classes = [IsReadOnly | IsAdminRole]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TitleViewSerializer
        return TitlePostSerializer


class ReviewView(viewsets.ModelViewSet):
    '''
    ViewSet to handle requests to
    the r'titles/(?P<title_id>\d+)/reviews' endpoint.
    Anyone has the permission to retrive an object.
    Only author, admin and moderator can modify an object.
    '''
    serializer_class = ReviewSerializer
    permission_classes = [RetrieveOnlyOrHasCUDPermissions]

    def perform_create(self, serializer):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title)

    def get_queryset(self):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        return title.reviews.all()


class CommentView(viewsets.ModelViewSet):
    '''
    ViewSet to handle requests to the
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments' endpoint.
    Anyone has the permission to retrive an object.
    Only author, admin and moderator can modify an object.
    '''
    serializer_class = CommentSerializer
    permission_classes = [RetrieveOnlyOrHasCUDPermissions]

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review,
            pk=self.kwargs.get('review_id'),
            title__pk=self.kwargs.get('title_id')
        )
        serializer.save(author=self.request.user, review=review)

    def get_queryset(self):
        review = get_object_or_404(
            Review,
            pk=self.kwargs.get('review_id'),
            title__pk=self.kwargs.get('title_id')
        )
        return review.comments.all()
