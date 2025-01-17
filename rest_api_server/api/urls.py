from django.urls import path
from api.views.file_views import FileUploadView, FileUploadChunksView, XMLFilterByCity, ListCSVFilesView, ConvertCSVtoXMLView, ValidateXMLView, XMLTextSearchView, SortXMLView, ListXMLFilesView
from .views.users import GetAllOrders, GetAllProducts

urlpatterns = [
    path('upload-file/', FileUploadView.as_view(), name='upload-file'),
    path('orders/', GetAllOrders.as_view(), name='orders'),
    path('upload-file/by-chunks', FileUploadChunksView.as_view(), name='upload-file-by-chunks'),    
    path('products/', GetAllProducts.as_view(), name='products'),
    path('xml/filter-by/', XMLFilterByCity.as_view(), name='xml-filter-by-city'),
    path('convert-csv-to-xml/', ConvertCSVtoXMLView.as_view(), name='convert-csv-to-xml'),
    path('validate-xml/', ValidateXMLView.as_view(), name='validate-xml'),
    path('xml-text-search/', XMLTextSearchView.as_view(), name='xml_text_search'),
    path('sort-xml/', SortXMLView.as_view(), name='sort-xml'),
    path('list-xml-files/', ListXMLFilesView.as_view(), name='list-xml-files'),
    path('list-csv-files/', ListCSVFilesView.as_view(), name='list-csv-files'),
    
]
