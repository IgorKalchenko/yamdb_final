from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from reviews.models import Category, Comment, Genre, Review, Title, User


class MeSerializer(serializers.ModelSerializer):
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
    CHOICES = User.CHOICES
    role = serializers.ChoiceField(
        read_only=False,
        choices=CHOICES,
        default=User.USER
    )


class ConfirmationCodeSerializer(serializers.Serializer):
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
    username = serializers.CharField(required=True, max_length=150)
    confirmation_code = serializers.CharField(max_length=150)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'slug')
        lookup_field = 'slug'


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('name', 'slug')
        lookup_field = 'slug'


class TitleViewSerializer(serializers.ModelSerializer):
    genre = GenreSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    rating = serializers.FloatField()

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description',
                  'genre', 'category', 'rating')


class TitlePostSerializer(serializers.ModelSerializer):
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
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        exclude = ('review',)
        model = Comment
