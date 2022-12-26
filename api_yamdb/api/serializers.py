from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from reviews.models import Category, Comment, Genre, Review, Title, User


class MeSerializer(serializers.ModelSerializer):
    '''
    Serializer to handle User instances for
    '.../users/me/' endpoint.
    '''
    role = serializers.CharField(read_only=True)
    username = serializers.CharField(
        required=True,
        max_length=150,
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message='Поле "username" должно быть уникальным'
        )]
    )
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message='Поле "email" должно быть уникальным'
        )]
    )

    class Meta:
        fields = (
            'username', 'email',
            'first_name', 'last_name',
            'bio', 'role'
        )
        model = User

    def validate_username(self, value):
        if value == 'me':
            raise serializers.ValidationError(
                'Поле "username" не может иметь значение "me".'
            )
        return value


class AdminUserSerializer(MeSerializer):
    '''
    Serializer to handle User instances.
    Inherits from MeSerializer.
    '''
    CHOICES = User.CHOICES
    role = serializers.ChoiceField(
        read_only=False,
        choices=CHOICES,
        default=User.USER
    )


class ConfirmationCodeSerializer(serializers.Serializer):
    '''
    Serializer used to handle data for
    the view function responsible for signup of new users.
    '''
    username = serializers.CharField(
        required=True,
        max_length=150
    )
    email = serializers.EmailField(
        required=True,
        max_length=254
    )
    confirmation_code = serializers.CharField(required=False, max_length=150)

    def validate_username(self, value):
        if value == 'me':
            raise serializers.ValidationError(
                'Поле "username" не может иметь значение "me".'
            )
        return value


class JWTTokenSerializer(serializers.Serializer):
    '''
    Serializer used to handle data for
    the view function responsible generating jwt tokens.
    '''
    username = serializers.CharField(required=True, max_length=150)
    confirmation_code = serializers.CharField(max_length=150)


class CategorySerializer(serializers.ModelSerializer):
    '''
    Serializer used to handle Category instances.
    '''
    class Meta:
        model = Category
        fields = ('name', 'slug')
        lookup_field = 'slug'


class GenreSerializer(serializers.ModelSerializer):
    '''
    Serializer used to handle Genre instances.
    '''
    class Meta:
        model = Genre
        fields = ('name', 'slug')
        lookup_field = 'slug'


class TitleViewSerializer(serializers.ModelSerializer):
    '''
    Serializer used to handle Title instances with
    list and retrieve ViewSet methods.
    '''
    genre = GenreSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    rating = serializers.FloatField()

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description',
                  'genre', 'category', 'rating')


class TitlePostSerializer(serializers.ModelSerializer):
    '''
    Serializer used to handle Title instances with
    create, destroy, update and partial update ViewSet methods.
    '''
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug',
        many=True
    )
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug',
    )

    class Meta:
        fields = '__all__'
        model = Title


class ReviewSerializer(serializers.ModelSerializer):
    '''
    Serializer used to handle Review instances.
    '''
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        exclude = ('title',)
        model = Review

    def validate(self, data):
        is_exist = Review.objects.filter(
            author=self.context['request'].user,
            title=self.context['view'].kwargs.get('title_id')).exists()
        if is_exist and self.context['request'].method == 'POST':
            raise serializers.ValidationError(
                'Запрещено добавление более одного отзыва на произведение.'
            )
        return data


class CommentSerializer(serializers.ModelSerializer):
    '''
    Serializer used to handle Comment instances.
    '''
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        exclude = ('review',)
        model = Comment
