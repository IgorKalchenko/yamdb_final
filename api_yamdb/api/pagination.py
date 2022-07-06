from rest_framework.pagination import PageNumberPagination


class ApiPagination(PageNumberPagination):
    page_size = 5
