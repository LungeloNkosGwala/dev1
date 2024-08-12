from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.urls import reverse
from django import forms
from django.db import transaction
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from warelogic_app.models import UserProfile,AccessLevels, Entity, RequestFunctions, ProductMaster, BinContent, Interim, ASNDelivery,ASNLines
import pandas as pd
import logging
from .forms import ProductSearchForm,BinSearchForm
from django.db.models import F,Q
from io import BytesIO
from openpyxl import load_workbook
from xlsxwriter import Workbook
import gc
from django.db import connection

# Create your views here.


@login_required
def index(request):
    return render(request, "warelogic_app/index.html")


@login_required
def createEntity(request):
    allEntity = Entity.objects.all()
    context = {"allEntity":allEntity}
    if "createEntity" in request.POST:
        client = request.POST['client']
        branch = request.POST['branch']
        entity = request.POST['entity']
        address = request.POST['address']

        Entity.createEntity(client,branch,entity,address)
        messages.success(request, "Entity successfully created")
        allEntity = Entity.objects.all()
        context = {"allEntity":allEntity}
        return render(request, "warelogic_app/systemcontrol/maintenance/entityupdate.html", context)
    return render(request, "warelogic_app/systemcontrol/maintenance/entityupdate.html",context)


@login_required
def indexScanner(request):
    return render(request, "warelogic_app/scanner_index.html")


def userLogin(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username,password=password)

        if user is not None:
            if user.is_active:
                if user.last_login is None:
                    login(request,user)
                    return redirect('change_password')
                else:
                    login(request,user)
                    return render(request, "warelogic_app/index.html")
            else:
                return HttpResponse("Account Not active")
        else:
            return HttpResponse("Invalid login details supplied")
    else:
        return render(request,"warelogic_app/login.html")



def userLoginScanner(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username,password=password)

        if user is not None:
            if user.is_active:
                if user.last_login is None:
                    login(request,user)
                    return redirect('change_password')
                else:
                    login(request,user)
                    return render(request, "warelogic_app/scanner_index.html")
            else:
                return HttpResponse("Account Not active")
        else:
            return HttpResponse("Invalid login details supplied")
    else:
        return render(request,"warelogic_app/scanner_login.html")


def userLogout(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))



def userLogoutScanner(request):
    logout(request)
    return HttpsResponseRedirect(reverse("scanner_index"))


@login_required
def change_password(request):
    if request.method == "POST" and "login_type" in request.POST:

        login_type = request.POST['login_type']

        form = PasswordChangeForm(request.user,request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user) #important
            messages.success(request, "Your password has successfully been updated")
            if login_type == "scanner":
                return redirect('logout_scanner')
            else:
                return redirect('logout')
        else:
            messages.error(request, "Please correct the error below")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "warelogic_app/password_change.html",{"form":form})
    

@login_required
def resetPassword(request):
    if request.method == "POST" and "username" in request.POST:
        username = request.POST['username']
        user_to_clear = get_object_or_404(User, username=username)
        user_to_clear.last_login = None
        user_to_clear.save()
        messages.success(request, f"{user_to_clear.username}\n Your last login has been cleared.")
        return render(request,"warelogic_app/systemcontrol/usermanagement/resetpassword.html")
    return render(request,"warelogic_app/systemcontrol/usermanagement/resetpassword.html")


@login_required
def registerUser(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, "warelogic_app/index.html")
    else:
        form = UserCreationForm()
    context = {"form":form}
    return render(request, "warelogic_app/systemcontrol/usermanagement/registeruser.html",context)


@login_required
def systemmaintenance(request):
    return render(request,"warelogic_app/systemcontrol/systemmaintenance.html")

@login_required
def usermanagement(request):
    return render(request, "warelogic_app/systemcontrol/usermanagement.html")

duty_option = ["NA","receiving","putaway","counting","picking","routing","shipping","clerk","technical"]
area_option = ["NA","MezzA","MezzB","Pallet","FPacker","BPacker"]
machine_option = ["NA","MHE","Trolly"]


@login_required
def userProfile(request):
    if "search" in request.GET:
        query = request.GET.get("username")
        userSearch = get_object_or_404(User, username=query)
        context = {"userSearch":userSearch}
        return render(request, "warelogic_app/systemcontrol/usermanagement/userprofile.html",context)
    elif "showProfile" in request.GET and "sel" in request.GET:
        user_id = request.GET.get("sel")
        if user_id == "":
           return render(request,"warelogic_app/systemcontrol/usermanagement/userprofile.html")
        profileResult = UserProfile.objects.all().filter(user_id = user_id)
        userSearch = get_object_or_404(User, id=user_id)

        user_entity = None
        duty = None
        area = None
        machine = None

        if profileResult:
            for i in profileResult:
                user_entity = Entity.objects.get(id=i.entity_id).entity
                duty = i.duty
                area = i.area
                machine = i.machine

        entity = Entity.objects.all()
        context = {"entity":entity,
                    "user_entity":user_entity,
                    "duty":duty,
                    "area":area,
                    "machine":machine,
                    "duty_option":duty_option,
                    "area_option":area_option,
                    "machine_option":machine_option,
                    "userSearch":userSearch}
        return render(request,"warelogic_app/systemcontrol/usermanagement/userprofile.html",context)
    else:
        if "profileUpdate" in request.GET:
            user_id = request.GET.get("profileUpdate")
            if user_id == "":
               return render(request,"warelogic_app/systemcontrol/usermanagement/userprofile.html")
            UserProfile.objects.filter(user_id=user_id).delete()
            UserProfile.objects.update_or_create(user_id=user_id,
                                                entity_id = Entity.objects.get(entity=request.GET.get("entity_sel")).id,
                                                duty = request.GET.get("duty_sel"),
                                                area = request.GET.get("area_sel"),
                                                machine = request.GET.get("machine_sel"))

            messages.success(request,"Profile Updated Sucessfully")

    return render(request,"warelogic_app/systemcontrol/usermanagement/userprofile.html")


class CsvImportForm(forms.Form):
    csv_upload = forms.FileField(label=".txt File Upload")


@login_required
def uploader(request, col_no: int):
    # Retrieve the uploaded file from the request
    csv_file = request.FILES.get('csv_upload')
    result = True

    # Check if the file is a .txt file
    if not csv_file or not csv_file.name.endswith(".txt"):
        return [], False

    # Read the file data
    try:
        file_data = csv_file.read().decode("utf-8")
    except UnicodeDecodeError:
        return [], False

    # Split the data into lines
    csv_data = file_data.strip().split("\n")

    data = []

    # Extract data from each column
    for line in csv_data:
        fields = line.split("\t")
        if len(fields) < col_no:
            return [], False
        data.append(fields[:col_no])

    # Create a DataFrame from the data
    try:
        df = pd.DataFrame(data)
        df.columns = df.iloc[0]
        df = df.drop(0).reset_index(drop=True)
    except Exception as e:
        return [], False

    return df, result


@login_required
def requestFunctions(request):
    if "requestfunctions" in request.POST:
        col_no = 5
        df, result = uploader(request, col_no)
        print(df)
        if result == False:
            messages.warning(request, "File Upload Error, Please check file type and content")
            return render(request,"warelogic_app/systemcontrol/maintenance/requestfunctions.html")
        failed_lines = []
        existingFunc = set(RequestFunctions.objects.values_list("requestfunction", flat=True))
        try:
            data_to_insert = []
            for index, row in df.iterrows():
                func = row.iloc[3]
                if func not in existingFunc:
                    instance = RequestFunctions(
                        usertypeall = row.iloc[0],
                        usertypedivision = row.iloc[1],
                        functiongroup = row.iloc[2],
                        requestfunction = func,
                        requestdesc = row.iloc[4]
                    )
                    data_to_insert.append(instance)
            batch_size = 500
            for batch in range(0, len(data_to_insert), batch_size):
                with transaction.atomic():
                    RequestFunctions.objects.bulk_create(data_to_insert[batch:batch + batch_size])
        except Exception as e:
            print(f"Error: {e}")
        finally:
            from django.db import connection
            connection.close()

        form = CsvImportForm()
        context = {"form":form}
        return render(request,"warelogic_app/systemcontrol/maintenance/requestfunctions.html",context)
    form = CsvImportForm()
    context = {"form":form}
    return render(request,"warelogic_app/systemcontrol/maintenance/requestfunctions.html",context)

@login_required         
def updateProductMaster(request):
    if "updateproductmaster" in request.POST:
        col_no = 8
        df, result = uploader(request, col_no)
        if result == False:
            messages.warning(request, "File Upload Error, Please check file type and content")
            return render(request,"warelogic_app/systemcontrol/maintenance/updateproductmaster.html")

        user = request.user
        try:
            entity_id = UserProfile.objects.get(user_id=user.id).entity_id
        except Exception as e:
            logging.error(f"Error updating Product Master: {e}")
            messages.error(request, "User does not have a Profile Update, please request Profile update")
            form = CsvImportForm()
            context = {"form":form}
            return render(request,"warelogic_app/systemcontrol/maintenance/updateproductmaster.html",context)

        entity_name = Entity.objects.get(id=entity_id).entity

        #Retrieve existing partnumber for the entity, using current user and entiry indicator
        existing_partnumbers = set(ProductMaster.objects.filter(entity_id=entity_id).values_list("partnumber", flat=True))
        existing_barcodes = set(ProductMaster.objects.filter(entity_id=entity_id).values_list("barcode", flat=True))

        skipped_items = []

        try:
            data_to_insert = []
            for index, row in df.iterrows():
                partnumber = row.iloc[0]
                barcode = row.iloc[3]

                if partnumber in existing_partnumbers or barcode in existing_barcodes:
                    skipped_items.append({
                        'partnumber': partnumber,
                        'description': row.iloc[1],
                        'category': row.iloc[2],
                        'barcode': barcode,
                        'packqty': row.iloc[4],
                        'uoiqty': row.iloc[5],
                        'costprice': row.iloc[6],
                        'salesprice': row.iloc[7]
                    })
                    continue

                instance = ProductMaster(
                    partnumber = partnumber,
                    description = row.iloc[1],
                    category = row.iloc[2],
                    barcode = barcode,
                    packqty = row.iloc[4],
                    uoiqty = row.iloc[5],
                    costprice = row.iloc[6],
                    salesprice = row.iloc[7],
                    entity_id = entity_id,
                    productcode = str(entity_name) + "-" +  str(partnumber),
                    status = True
                )
                data_to_insert.append(instance)
            batch_size = 500
            for batch in range(0, len(data_to_insert), batch_size):
                with transaction.atomic():
                    ProductMaster.objects.bulk_create(data_to_insert[batch:batch + batch_size])
            messages.success(request, "Product Master updated successfully")
        except Exception as e:
            logging.error(f"Error updating Product Master: {e}")
            messages.error(request, "An error occurred while updating the Product Master. Please try again.")
        finally:
            from django.db import connection
            connection.close()

        # Export skipped items to Excel
        if skipped_items:
            skipped_df = pd.DataFrame(skipped_items)
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                skipped_df.to_excel(writer, index=False, sheet_name='Skipped Items')

            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="skipped_items.xlsx"'
            return response

        

        form = CsvImportForm()
        context = {"form":form}
        return render(request,"warelogic_app/systemcontrol/maintenance/updateproductmaster.html",context)

    elif "partnumber" in request.POST and "submit" in request.POST and "delete" in request.POST:
        entity_id = UserProfile.objects.get(user_id=request.user).entity_id
        search_term = request.POST['partnumber']
        item = ProductMaster.checkitem(search_term,entity_id)
        if item:
            delResult = ProductMaster.objects.all().filter(Q(partnumber=search_term)|
                                                                Q(productcode=search_term)|
                                                                Q(barcode=search_term),
                                                                entity_id=entity_id).first()

            allqty = int(delResult.sohqty) + int(delResult.createdeliveryqty) + int(delResult.onholdqty) + int(delResult.reconqty)
            if allqty != 0:
                messages.warning(request,"Error, you can delete item {} no Zero quantities on stock".format(delResult.productcode))
            else:
                delResult.delete()
                messages.success(request, "Item {} was been successfully cleared from Product Master".format(delResult.productcode))

    form = CsvImportForm()
    context = {"form":form}
    return render(request,"warelogic_app/systemcontrol/maintenance/updateproductmaster.html",context)    

@login_required
def productInquire(request):
    form = ProductSearchForm()
    context = {"form":form}
    if "search" in request.POST:

        entity_id = get_object_or_404(UserProfile, user=request.user).entity_id


        form = ProductSearchForm(request.POST)
        context = {"form":form}
        if form.is_valid():
            search_term = form.cleaned_data['search_term']
            item = ProductMaster.checkitem(search_term,entity_id)

            if item:
                searchResult = ProductMaster.objects.all().filter(Q(partnumber=search_term)|Q(productcode=search_term)|Q(barcode=search_term),
                                                                    entity_id=entity_id)

                try:
                    criteria = list(BinContent.objects.filter(entity_id=entity_id).values_list("area",'sut',"abc").distinct())

                    area = []
                    sut = []
                    abc = []
                    if not criteria:
                        area = []
                        sut = []
                        abc = []
                    else:
                        for area_values, sut_values, abc_values in criteria:
                            area.append(area_values)
                            sut.append(sut_values)
                            abc.append(abc_values)

                        area = list(set(area))
                        sut = list(set(sut))
                        abc = list(set(abc))

                        context = {
                            'area':area,
                            'sut':sut,
                            'abc':abc,
                            "searchResult":searchResult,
                            "form":form
                        }

                        return render(request,"warelogic_app/inquire/productinquire.html",context)
                finally:
                    del abc, sut, area, criteria
                    gc.collect()  

                context = {
                    "searchResult":searchResult,
                    "form":form
                }
                return render(request,"warelogic_app/inquire/productinquire.html",context)


            messages.warning(request,"Error, item doesn't exist")
            return render(request,"warelogic_app/inquire/productinquire.html")

    elif "updatepfep" in request.POST:
        productcode = request.POST['updatepfep']
        try:
            abc_sel = request.POST['abc_sel']
            area_sel = request.POST['area_sel']
            sut_sel = request.POST['sut_sel']
        except Exception as e:
            logging.error(f"Form not complete: {e}")
            messages.error(request, "Your form request is incomplete.")
            return render(request,"warelogic_app/inquire/productinquire.html",{"form":form})

        entity_id = get_object_or_404(UserProfile, user=request.user).entity_id

        try:
            ProductMaster.updatepfep(entity_id,productcode,area_sel,sut_sel,abc_sel)
            messages.success(request,"PFEP for {} has successfully been update".format(productcode))
        except Exception as e:
            logging.error(f"Error in updating PFEP: {e}")
            messages.error(request, "An error occurred while updating the PFEP. Please try again.")
        finally:
            from django.db import connection
            connection.close()

        searchResult = ProductMaster.objects.all().filter(Q(partnumber=productcode)|Q(productcode=productcode)|Q(barcode=productcode),
                                                            entity_id=entity_id)
        context = {
            "searchResult":searchResult,
            "form":form
        }

    return render(request,"warelogic_app/inquire/productinquire.html",context)

@login_required
def updateBinLocation(request):
    if "updatebinlocation" in request.POST:
        col_no = 7
        df, result = uploader(request, col_no)

        if result == False:
            messages.warning(request, "File Upload Error, Please check file type and content")
            return render(request,"warelogic_app/systemcontrol/maintenance/updatebinlocation.html")

        user = request.user
        try:
            entity_id = UserProfile.objects.get(user_id=user.id).entity_id
        except Exception as e:
            logging.error(f"Error updating Product Master: {e}")
            messages.error(request, "User does not have a Profile Update, please request Profile update")
            form = CsvImportForm()
            context = {"form":form}
            return render(request,"warelogic_app/systemcontrol/maintenance/updatebinlocation.html",context)

        entity_name = Entity.objects.get(id=entity_id).entity

        #Retrieve existing partnumber for the entity, using current user and entiry indicator
        existing_binns = set(BinContent.objects.filter(entity_id=entity_id).values_list("binn", flat=True))
        
        skipped_items = []

        try:
            data_to_insert = []
            for index, row in df.iterrows():
                binn = row.iloc[0]

                mixedbin = row.iloc[6].strip().lower()
                if mixedbin in ['true',"1"]:
                    mixedbin = True
                elif mixedbin in ['false','0']:
                    mixedbin = False
                else:
                    messages.error(request,f"Invalid boolen value '{mixedbin}' in row {index +1}")


                if binn in existing_binns:
                    skipped_items.append({
                        'binn': binn,
                        'area': row.iloc[1],
                        'sut': row.iloc[2],
                        'abc': row.iloc[3],
                        'puawayseq': row.iloc[4],
                        'orderseq': row.iloc[5],
                        "mixedbin": mixedbin
                    })
                    continue

                instance = BinContent(
                    binn = binn,
                    area = row.iloc[1],
                    sut = row.iloc[2],
                    abc = row.iloc[3],
                    putawayseq = row.iloc[4],
                    orderseq = row.iloc[5],
                    mixedbin = mixedbin,
                    entity_id = entity_id,
                    binlocation = str(entity_name) + "-" +  str(binn),
                )
                data_to_insert.append(instance)
            batch_size = 500
            for batch in range(0, len(data_to_insert), batch_size):
                with transaction.atomic():
                    BinContent.objects.bulk_create(data_to_insert[batch:batch + batch_size])
            messages.success(request, "Bin Content updated successfully")
        except Exception as e:
            logging.error(f"Error in updating Bin Content: {e}")
            messages.error(request, "An error occurred while updating the Bin Content. Please try again.")
        finally:
            from django.db import connection
            connection.close()

        # Export skipped items to Excel
        if skipped_items:
            skipped_df = pd.DataFrame(skipped_items)
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                skipped_df.to_excel(writer, index=False, sheet_name='Skipped Items')

            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="skipped_items.xlsx"'
            return response

        form = CsvImportForm()
        context = {"form":form}
        return render(request,"warelogic_app/systemcontrol/maintenance/updatebinlocation.html",context)

    elif "binn" in request.POST and "submit" in request.POST and "delete" in request.POST:
        entity_id = UserProfile.objects.get(user_id=request.user).entity_id
        search_term = request.POST['binn']
        item = BinContent.checkbin(search_term,entity_id)
        if item:
            delResult = BinContent.objects.all().filter(Q(binn=search_term)|Q(binlocation=search_term),entity_id=entity_id).first()

            
            if delResult.sohqty != 0 or delResult.routed == True:
                messages.warning(request,"Error, you can delete item {} with non-Zero quantities on stock or routed".format(delResult.binlocation))
            else:
                delResult.delete()
                messages.success(request, "Item {} was been successfully cleared from Bin Content".format(delResult.binlocation))


    form = CsvImportForm()
    context = {"form":form}
    return render(request,"warelogic_app/systemcontrol/maintenance/updatebinlocation.html",context)

@login_required
def binInquire(request):
    formP = ProductSearchForm()
    formB = BinSearchForm
    context = {"formP":formP,"formB":formB}

    entity_id = get_object_or_404(UserProfile, user=request.user).entity_id

    if "binsearch" in request.POST:

        formB = BinSearchForm(request.POST)
        if formB.is_valid():
            search_term = formB.cleaned_data['search_term']
            item = BinContent.checkbin(search_term,entity_id)
            if item:
                searchResultB = BinContent.objects.all().filter(Q(binn=search_term)|Q(binlocation=search_term),entity_id=entity_id).first()

                try:
                    productcode = searchResultB.productcode.productcode
                except Exception as e:
                    productcode = None
                context = {
                    "searchResultB":searchResultB,
                    "formP":formP,
                    "formB":formB,
                    "productcode":productcode
                }
                
                return render(request,"warelogic_app/inquire/bininquire.html",context)
            messages.warning(request,"Error, Bin doesn't exist")
            return render(request,"warelogic_app/inquire/bininquire.html",context)
        messages.warning(request,"Error, Form is invalid")

    elif "productsearch" in request.POST:

        formP = ProductSearchForm(request.POST)
        if formP.is_valid():
            search_term = formP.cleaned_data['search_term']
            item = ProductMaster.checkitem(search_term,entity_id)

            if item:
                item_id = ProductMaster.objects.get(Q(partnumber=search_term)|Q(productcode=search_term)|Q(barcode=search_term),
                                                                    entity_id=entity_id).id

                searchResultP = BinContent.objects.filter(productcode_id=item_id)

                if searchResultP:

                    productcode = searchResultP.first().productcode.productcode
                    context = {
                        "searchResultP":searchResultP,
                        "formP":formP,
                        "formB":formB,
                        "productcode":productcode,
                    }
                    return render(request,"warelogic_app/inquire/bininquire.html",context)
                
                messages.warning(request,"Error, Item is not in bin locations")
                return render(request,"warelogic_app/inquire/bininquire.html",context)
                
            messages.warning(request,"Error, Bin doesn't exist")
            return render(request,"warelogic_app/inquire/bininquire.html",context)
        
        messages.warning(request,"Error, Form is invalid")
    return render(request,"warelogic_app/inquire/bininquire.html",context)

@login_required
def loadASN(request):
    return render(request, "warelogic_app/inbound/loadasn.html")

@login_required
def asnItemSelect(request):
    form = ProductSearchForm()
    entity_id = get_object_or_404(UserProfile, user=request.user).entity_id
    user_id = request.user.id
    asnStaging = Interim.objects.filter(interimtype="ASNStaging",entity_id=entity_id, user_id = user_id)
    context = {"asnStaging":asnStaging,"form":form}
    if "search" in request.GET:
        form = ProductSearchForm(request.GET)
        context = {"asnStaging":asnStaging,"form":form}
        if form.is_valid():
            search_term = form.cleaned_data['search_term']
            item = ProductMaster.checkitem(search_term,entity_id)

            if item:
                searchResult = ProductMaster.objects.filter(Q(partnumber=search_term)|Q(productcode=search_term)|Q(barcode=search_term),
                                                                    entity_id=entity_id)
                context = {"searchResult":searchResult,"asnStaging":asnStaging}
                return render(request, "warelogic_app/inbound/loadasn/asnitemselect.html",context)
            messages.error(request, "Error, Item {} doesn't exist".format(search_term))
            return render(request, "warelogic_app/inbound/loadasn/asnitemselect.html",context)
    elif "stage" in request.GET and "sel" in request.GET:
        productcode_id = request.GET.get("sel")
        qty = int(request.GET.get("qty"))
        existing_staging = Interim.objects.filter(interimtype="ASNStaging",entity_id=entity_id, user_id = request.user,productcode_id=productcode_id)
        hu = ""
        parent = ""
        route = ""
        interimtype="ASNStaging"
        try:
            if existing_staging:
                Interim.updateqty(entity_id,interimtype,parent,productcode_id,qty,route,hu,user_id)
                messages.success(request, "Interim transaction successfully updated")
            else:
                Interim.createInterim(entity_id,interimtype,parent,productcode_id,qty,route,hu,user_id)
                messages.success(request, "Interim transaction successfully staged")
                
            
        except Exception as e:
            logging.error(f"Error transacting on Interim model: {e}")
            messages.error(request, "Error transacting on the Imterim model, please log error with Administrator")
        
        asnStaging = Interim.objects.filter(interimtype="ASNStaging",entity_id=entity_id, user_id = request.user)
        context = {"asnStaging":asnStaging,"form":form}
        return render(request, "warelogic_app/inbound/loadasn/asnitemselect.html",context)

    elif "delete" in request.GET and "sel_delete" in request.GET:
        productcode_id = request.GET.get("sel_delete")

        hu = ""
        parent = ""
        route = ""
        interimtype="ASNStaging"

        Interim.deleteEntry(entity_id,interimtype,parent,productcode_id,route,hu,user_id)
        asnStaging = Interim.objects.filter(interimtype="ASNStaging",entity_id=entity_id, user_id = request.user)
        messages.success(request, "Item has successsfully been deleted from {}".format(interimtype))
        context = {"asnStaging":asnStaging,"form":form}

            
    return render(request, "warelogic_app/inbound/loadasn/asnitemselect.html",context)

@login_required
def asnCreate(request):
    entity_id = get_object_or_404(UserProfile, user=request.user).entity_id
    entity = Entity.objects.get(id=entity_id).entity
    user_id = request.user.id
    asnStaging = Interim.objects.filter(interimtype="ASNStaging",entity_id=entity_id, user_id = user_id)

    total_sales = 0
    total_cost = 0
    total_lines = 0
    total_qty = 0

    no = 100000
    asnno = 'ASN'+str(no)
    
    if asnStaging:
        existing_delivery = ASNDelivery.objects.filter().last()
        if existing_delivery:
            el = existing_delivery.asnno
            el = int(el[3:])+1
            asnno = "ASN"+str(el)


        productmaster = ProductMaster.objects.filter(entity_id=entity_id)

        for item in asnStaging:
            total_sales = total_sales +(int(item.qty)*productmaster.get(id=item.productcode_id).salesprice)
            total_cost = total_cost+ (int(item.qty)*productmaster.get(id=item.productcode_id).costprice)
            total_lines = total_lines + 1
            total_qty = total_qty+int(item.qty)

    asntype = ["Local","Import","Return"]
    context = {"entity":entity,
                "asnno":asnno,
                "total_sales":total_sales,
                "total_cost":total_cost,
                "total_lines":total_lines,
                "total_qty":total_qty,
                "asntype":asntype}
        
    if "asnCreate" in request.GET:
        asntype_sel = request.GET.get('asntype_sel')
        supplier = request.GET.get('supplier')
        invoice = request.GET.get('invoice')
        reference = request.GET.get('reference')
        if asnStaging:

            try:
                ASNDelivery.createASN(entity_id,asnno,asntype_sel,supplier,reference,invoice,user_id,total_sales,total_lines,total_qty)

                asnno_id = ASNDelivery.objects.get(asnno=asnno).id

                messages.success(request, "ASN has successfully been created")
            except Exception as e:
                logging.error(f"Error creating ASN: {e}")
                messages.error(request, "An error occurred while creating an ASN. Please try again.")

            try:
                data_to_insert = []
                for entry in asnStaging:
                    instance = ASNLines(
                        asnno_id = asnno_id,
                        productcode_id = entry.productcode_id,
                        totalqty = entry.qty,
                        status = "ASNCreated"
                    )
                    data_to_insert.append(instance)
                batch_size = 500
                for batch in range(0, len(data_to_insert), batch_size):
                    with transaction.atomic():
                        ASNLines.objects.bulk_create(data_to_insert[batch:batch + batch_size])

                Interim.objects.filter(interimtype="ASNStaging",entity_id=entity_id, user_id = user_id).delete()
                messages.success(request, "ASNLines updated successfully")
            except Exception as e:
                logging.error(f"Error updating ASNLines: {e}")
                messages.error(request, "An error occurred while updating the ASNLines. Please try again.")

        messages.error(request, "Error, no selected asn items found.")

    return render(request, "warelogic_app/inbound/loadasn/asncreate.html",context)











