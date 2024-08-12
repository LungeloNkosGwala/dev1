from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.db.models import F,Q
from django.db.models import DO_NOTHING
from datetime import datetime
import pytz

sa_tz = pytz.timezone('Africa/Johannesburg')
date = datetime.now(sa_tz)


# Create your models here.

def set_default_password(sender, instance, **kwargs):
    if not instance.pk:
        instance.set_password('1234')

models.signals.pre_save.connect(set_default_password, sender=User)


class Entity(models.Model):
    client = models.CharField(max_length=50)
    branch = models.CharField(max_length=50)
    entity = models.CharField(max_length=3, unique=True)
    address = models.CharField(max_length=100)

    @classmethod
    def createEntity(self,client,branch,entity,address):
        self.objects.update_or_create(client=client,
                                        branch=branch,
                                        entity=entity,
                                        address=address)

class UserProfile(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    duty = models.CharField(max_length=50)
    area = models.CharField(max_length=50)
    machine = models.CharField(max_length=50)


class RequestFunctions(models.Model):
    usertypeall = models.CharField(max_length=50)
    usertypedivision = models.CharField(max_length=50)
    functiongroup = models.CharField(max_length=50)
    requestfunction = models.CharField(max_length=50, unique=True)
    requestdesc = models.CharField(max_length=200)


class AccessLevels(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    usertypeall = models.CharField(max_length=50)
    usertypedivision = models.CharField(max_length=50)
    functiongroup = models.CharField(max_length=50)
    requestfunction = models.ForeignKey(RequestFunctions,on_delete=models.CASCADE)



class ProductMaster(models.Model):
    entity = models.ForeignKey(Entity,on_delete=models.CASCADE)
    partnumber = models.CharField(max_length=50)
    productcode = models.CharField(max_length=50,unique=True)
    description = models.CharField(max_length=100)
    category = models.CharField(max_length=30)
    barcode = models.CharField(max_length=50)
    packqty = models.IntegerField(default=1)
    uoiqty = models.IntegerField(default=1)
    costprice = models.FloatField(default=0)
    salesprice = models.FloatField(default=0)
    area = models.CharField(max_length=30)
    sut = models.CharField(max_length=30)
    abc = models.CharField(max_length=3)
    createdeliveryqty = models.IntegerField(default=0)
    inboundqty = models.IntegerField(default=0)
    outboundqty = models.IntegerField(default=0)
    allocatedqty = models.IntegerField(default=0)
    onholdqty = models.IntegerField(default=0)
    reconqty = models.IntegerField(default=0)
    availqty = models.IntegerField(default=0)
    sohqty = models.IntegerField(default=0)
    status = models.BooleanField(default=True)

    def updatesohqty(self, *args,**kwargs):
        self.sohqty = self.inboundqty + self.outboundqty + self.availqty + self.allocatedqty
        super().save(*args, **kwargs)


    @classmethod
    def checkitem(self,search_term,entity_id):
        item = self.objects.filter(Q(partnumber=search_term)|Q(productcode=search_term)|Q(barcode=search_term),entity_id=entity_id).exists()
        return item

    @classmethod
    def updatepfep(self,entity_id,productcode,area_sel,sut_sel,abc_sel):
        self.objects.filter(entity_id=entity_id,productcode=productcode).update(area=area_sel,sut=sut_sel,abc=abc_sel)



class ASNDelivery(models.Model):
    entity = models.ForeignKey(Entity,on_delete=models.DO_NOTHING)
    asnno = models.CharField(max_length=30, unique=True)
    deliveryno = models.CharField(max_length=30)
    asntype = models.CharField(max_length=30)
    supplier = models.CharField(max_length=50)
    reference = models.CharField(max_length=30)
    invoiceno = models.CharField(max_length=30)
    createdate = models.DateTimeField(null=False, blank=False)
    deliverydate = models.DateTimeField(null=True, blank=True)
    grndate = models.DateTimeField(null=True, blank=True)
    createuser = models.ForeignKey(User,on_delete=models.DO_NOTHING)
    deliveryuser = models.CharField(max_length=30)
    assignuser1 = models.CharField(max_length=30)
    assignuser2 = models.CharField(max_length=30)
    assignuser3 = models.CharField(max_length=30)
    totallines = models.IntegerField(default=0)
    totalqty = models.IntegerField(default=0)
    totalsales = models.FloatField(default=0)
    linesreceived = models.IntegerField(default=0)
    linesputaway = models.IntegerField(default=0)
    receivedqty = models.IntegerField(default=0)
    putawayqty = models.IntegerField(default=0)
    status = models.CharField(max_length=30)

    @classmethod
    def createASN(cls,entity_id,asnno,asntype_sel,supplier,reference,invoice,user_id,total_sales,total_lines,total_qty):
        cls.objects.create(
            entity_id=entity_id,
            asnno= asnno,
            asntype = asntype_sel,
            supplier = supplier,
            reference = reference,
            invoiceno=invoice,
            createdate=date,
            createuser_id = user_id,
            totallines = total_lines,
            totalsales = total_sales,
            totalqty = total_qty,
            status = "ASNCreated"
        )

class ASNLines(models.Model):
    asnno = models.ForeignKey(ASNDelivery, on_delete=models.CASCADE)
    productcode = models.ForeignKey(ProductMaster, on_delete=models.DO_NOTHING)
    totalqty = models.IntegerField(default=0)
    receivedqty = models.IntegerField(default=0)
    putawayqty = models.IntegerField(default=0)
    shortqty = models.IntegerField(default=0)
    extraqty = models.IntegerField(default=0)
    damagedqty = models.IntegerField(default=0)
    status = models.CharField(max_length=30)

class BinContent(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    binn = models.CharField(max_length=30)
    binlocation = models.CharField(max_length=30, unique=True)
    area = models.CharField(max_length=50)
    sut = models.CharField(max_length=30)
    abc = models.CharField(max_length=30)
    putawayseq = models.IntegerField(default=0)
    orderseq = models.IntegerField(default=0)
    productcode = models.ForeignKey(ProductMaster,null=True,blank=True,on_delete=models.DO_NOTHING)
    hu = models.CharField(max_length=30)
    sohqty = models.IntegerField(default=0)
    availqty = models.IntegerField(default=0)
    ageing = models.IntegerField(default=0)
    full = models.BooleanField(default=False)
    allocated = models.BooleanField(default=False)
    routed = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    mixedbin = models.BooleanField(default=True)

    @classmethod
    def checkbin(self,search_term,entity_id):
        item = self.objects.filter(Q(binn=search_term)|Q(binlocation=search_term),entity_id=entity_id).exists()
        return item

    


class Interim(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    interimtype = models.CharField(max_length=30)
    parent = models.CharField(max_length=30)
    productcode = models.ForeignKey(ProductMaster, on_delete=models.CASCADE)
    qty = models.IntegerField(default=0)
    route = models.CharField(max_length=30)
    hu = models.CharField(max_length=30)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    date = models.DateTimeField(null=False,blank=False)

    @classmethod
    def updateqty(self,entity_id,interimtype,parent,productcode_id,qty,route,hu,user_id):
        self.objects.filter(entity_id=entity_id,
                            interimtype=interimtype,
                            productcode_id=productcode_id,
                            route=route,
                            hu=hu,
                            user_id=user_id).update(qty=qty)

    @classmethod
    def createInterim(cls,entity_id,interimtype,parent,productcode_id,qty,route,hu,user_id):
        cls.objects.create(entity_id=entity_id,
                            interimtype=interimtype,
                            productcode_id=productcode_id,
                            route=route,
                            qty=qty,
                            hu=hu,
                            user_id=user_id,
                            date=date)
    @classmethod
    def deleteEntry(self,entity_id,interimtype,parent,productcode_id,route,hu,user_id):
        self.objects.filter(entity_id=entity_id,
                            interimtype=interimtype,
                            productcode_id=productcode_id,
                            route=route,
                            hu=hu,
                            user_id=user_id).delete()


    








    



