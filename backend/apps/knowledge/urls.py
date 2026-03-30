from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, upload_document, query_knowledge_view, knowledge_stats

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')

urlpatterns = [
    path('upload/', upload_document, name='knowledge-upload'),
    path('query/', query_knowledge_view, name='knowledge-query'),
    path('stats/', knowledge_stats, name='knowledge-stats'),
    path('', include(router.urls)),
]
