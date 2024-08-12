from django.urls import path, include
from warelogic_app import views

urlpatterns = [
    path("index/",views.index,name='index'),
    path("userLogin",views.userLogin, name='userLogin'),
    path("systemcontrol/systemmaintenance/",views.systemmaintenance,name="systemmaintenance"),
    path("systemcontrol/usermanagement/", views.usermanagement,name="usermanagement"),
    path('change_password/', views.change_password, name='change_password'),
    path("registerUser/", views.registerUser, name = "registerUser"),
    path("resetPassword/", views.resetPassword, name = "resetPassword"),
    path("userProfile/",views.userProfile, name="userProfile"),
    path("createEntity/", views.createEntity, name="createEntity"),
    path("requestFunctions/", views.requestFunctions, name="requestFunctions"),
    path("updateproductmaster/", views.updateProductMaster, name="updateProductMaster"),
    path("productinquire/", views.productInquire, name="productInquire"),
    path("updatebinlocation/",views.updateBinLocation, name="updateBinLocation"),
    path("bininquire/", views.binInquire, name="binInquire"),
    path("loadasn/",views.loadASN,name='loadASN'),
    path("asnitemselect/", views.asnItemSelect, name="asnItemSelect"),
    path("asncreate/", views.asnCreate, name='asnCreate'),
]