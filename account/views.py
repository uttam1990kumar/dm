from urllib import response
from django.shortcuts import  get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import *
from django.db.models import Q
import random 
from django.db.models import Count
from .serializers import *
from .send_otp import *
import os
from age import *
from dotenv import load_dotenv
# Create your views here.
load_dotenv('.env')
#print(os.getenv("Phone_nuber_exists_message"))

def connection(**kwargs):
    return kwargs
"""UPLOAD BANNER IMAGE"""
class Banner(APIView):
    def get(self,request):
        serializers=BannerSerializer(BannerImage.objects.all())
        return Response(serializers.data)
    def post(self,request):
        data=request.data 
        serializers=BannerSerializer(data=data)
        if serializers.is_valid():
            serializers.save()
            return Response(serializers.data,status=200)
        else:
            print(serializers.errors)
            return Response(serializers.errors)
    
    def put(self,request):
        data=request.data 
        bannerid=request.GET['id']
        banner=BannerImage.objects.get(id=bannerid)
        serializers=BannerSerializer(banner,data=data,partial=True)
        if serializers.is_valid():
            serializers.save()
            return Response(serializers.data,status=200)
        else:
            print(serializers.errors)
            return Response(serializers.errors)
        
    def delete(self,request):
        bannerid=request.GET['id']
        try:
            BannerImage.objects.get(id=bannerid).delete() 
        except Exception as e:
            return Response({"message":"Banner deleted"}) 


"""This function for  view profile check"""
def ViewedProfiles(matrimonyid,requestid,status=None):
    """self matrimony id"""
    selfprofile=get_object_or_404(Person,matrimony_id=matrimonyid)
    
    """requested matrimony id"""
    requested_profile=get_object_or_404(Person,matrimony_id=requestid)
    
    view_profile=ViewedProfile.objects.filter(profile__id=selfprofile.id)
    if status is None:                  
        if view_profile.exists():
            if view_profile[0].view.filter(id=requested_profile.id).exists():
                pass
            else:
                view_profile[0].view.add(requested_profile)
        else:
            
            view_profile=ViewedProfile.objects.create(profile=selfprofile)
            view_profile.view.add(requested_profile)
        return True
    elif status is not None:
        if view_profile.exists():
            return view_profile[0].view.filter(id=requested_profile.id).exists()
        else:
            return False

"""check request status"""       
def connect_status(matrimonyid,requestid):
    # assert matrimonyid is None ,"matrimony id can't be None"
    # assert requestid is None ," requested matrimony id can't be None"
    query=Q(
        Q(profile__matrimony_id=matrimonyid,requested_matrimony_id=requestid)
        |
        Q(profile__matrimony_id=requestid,requested_matrimony_id=matrimonyid)
    )
    send_friend_request=FriendRequests.objects.filter(query)
    if send_friend_request.exists():
        return {"connect_status":send_friend_request[0].request_status} 
    else:
        return {"connect_status":"connect"}   
        
def height_and_age(h,age):
   
    if h is not None and age is not None:
        return {"age":get_age(age),'height':height(h)}   
    elif h is None and age is None:
        return {"age":None,'height':None}    
    elif age is None:
        return {"age":None,'height':height(h)}
    elif h is None:
        return {"age":get_age(age),'height':None}

class Check_Phone_Number(APIView):
    def get(self,request):
        person_phone_number=Person.objects.filter(phone_number__iexact=request.GET['phone_number'])
        if person_phone_number.exists():
            generate_otp=random.randint(1000,9999)
            sending_otp(generate_otp,request.GET['phone_number'])
            return Response({"message":"OTP send successfully",
                             "status":person_phone_number[0].status,
                             "matrimony_id":person_phone_number[0].matrimony_id                             
                             },status=200)
        else:
            return Response({"message":"Accepted",
                            "status":False,
                            "matrimony_id":None                            
                             },status=200)

class Check_Email(APIView):
    def get(self,request):
        person_email=Person.objects.filter(email__iexact=request.GET['email'])
        if person_email.exists():
            return Response({"message":os.environ.get("Email_Exists"),
                            "status":person_email[0].status,
                            "matrimony_id":person_email[0].matrimony_id ,
                             
                             },status=200)
        else:
            return Response({"message":"Accepted",
                             "status":False ,
                            "matrimony_id":None                            
                             },status=200)
 

          
class Nation(APIView):
    def get(self,request):
        query=request.GET.get('q')
        response={}
        if query:
            cities=City.objects.filter(state__name=query)
            return Response([{"id":city.id,"name":city.name} for city in cities])    
        else:
            states=State.objects.all()
            return Response([{"id":state.id,"name":state.name} for state in states]) 
                
"""Single Profile get"""
class SingleProfile(APIView):
    def get(self,request):
        matrimonyid=request.GET['matrimony_id']
        requestid=request.GET['requeted_matrimony_id']
        
        profile=Person.objects.filter(matrimony_id=requestid)
        if profile.exists():
            images=ProfileMultiImage.objects.filter(profile__id=profile[0].id)
           
            #bookmark
            bookmark=Bookmark.objects.filter(profile__matrimony_id=matrimonyid,album__matrimony_id=requestid)
            #view profile
            ViewedProfiles(matrimonyid,requestid)
            serializers=ProfileSerializer(profile[0],many=False).data
            serializers['profileimage']=[
                {"id":image.id,"image":image.files.url if image.files else None}
                for image in images ]
            
            serializers['bookmark']= True if bookmark.exists() else False
            serializers.update(connect_status(matrimonyid,requestid))
            serializers.update(height_and_age( profile[0].height,profile[0].dateofbirth ))
            return Response(serializers)
        else:
            return Response({"message":"Invalid Matrimony Id","status":False},status=400)
       
"""Registration for new user"""
class Registration(APIView):
    def get(self,request):
        matrimonyid=request.GET.get('matrimony_id')
        if matrimonyid is not None:
            profile=Person.objects.filter(matrimony_id=matrimonyid)
            if profile.exists():
                images=ProfileMultiImage.objects.filter(profile__id=profile[0].id)
                serializers=ProfileSerializer(profile[0],many=False).data
                serializers['profileimage']=[
                    {"id":image.id,"image":image.files.url if image.files else None}
                    for image in images ]
                return Response(serializers)
            else:
                return Response({"message":"Invalid Matrimony Id","status":False},status=400)
        else: 
            profiles=Person.objects.all().order_by("-id")
            response={}
            for profile in profiles:
                images=ProfileMultiImage.objects.filter(profile__id=profile.id)
                serializers=ProfileSerializer(profile,many=False).data
                serializers['profileimage']=[
                    {"id":image.id,"image":image.files.url if image.files else None}
                    for image in images ]
                serializers.update(height_and_age( profile.height,profile.dateofbirth ))
                response[profile.id]=serializers
            return Response(response.values())
    
    def post(self,request):
        if not request.POST._mutable:
            request.POST._mutable=True
           
        data=request.data 
        try:
            phone=data['phone_number']
            email=data['email']
        except KeyError as msg:
            return Response({"message":os.environ.get("Key_Not_Found"),"KeyError":str(msg),"status":False})
        person_phone_number=Person.objects.filter(phone_number__iexact=phone)
        if person_phone_number.exists():
            return Response({"message":os.environ.get("Phone_Number_Exists_Message"),
                             "status":person_phone_number[0].status,
                             "matrimony_id":person_phone_number[0].matrimony_id,
                             "phone_number":person_phone_number[0].phone_number
                             })
        person_email=Person.objects.filter(email__iexact=email)
        if person_email.exists():
            return Response({"message":os.environ.get("Email_Exists"),
                             "status":person_email[0].status,
                            "matrimony_id":person_email[0].matrimony_id,
                             "email":person_email[0].email
                             })
        serializers=PersonSerializers(data=data)
        if serializers.is_valid():
            serializers.save()
            return Response({"message":os.environ.get("Profile_Created"),
                             "phone_number":phone
                             })
        else:
            print(serializers.errors)
            return Response(serializers.errors,status=400)
        
    def delete(self,request):
        #matrimonyid=request.GET['matrimony_id']
        person=Person.objects.filter(matrimony_id=request.GET['matrimony_id'])
        if person.exists():
            person.delete()
            
            return Response({"message":"Profile Deleted sucessfully",'status':True})
        else:
            return Response({"message":"Profile Matrimony Id Not Found",'status':False})


"""VALIDATE OTP AUTHENTICATION AND LOGIN WITH OTP""" 
"""api/auth/otp"""
class Validate_OTP(APIView):
    def post(self,request) :
        data=request.data

        try:
           
            data['phone_number']
            data['otp']
            
        except KeyError as msg:
            return Response({"message":str(msg),"status":False,"required_field":True})
        
        
        contactnumber= Person.objects.get(phone_number__iexact=data['phone_number'])    
       
        saved_otp=SaveOTP.objects.get(phone_number__iexact=data['phone_number'])
        images=ProfileMultiImage.objects.filter(profile=contactnumber)
        
        """OTP VARIFICATION """
        if int(data['otp'])==saved_otp.otp:
            
            if data['phone_number'] != "8500001406":
             
                saved_otp.delete()

                contactnumber.status=True

                contactnumber.save()
        
            response={
                "message":"Login successfully",
                "phone_number":contactnumber.phone_number,
                "name":contactnumber.name,
                "matrimony_id":contactnumber.matrimony_id,
                "image":images[0].files.url if images.exists() else None,
                "status":contactnumber.status,
                }
            return Response(response,status=status.HTTP_202_ACCEPTED)
            
        else:
            return Response({"message":"Enter wrong otp","status":False},status=status.HTTP_404_NOT_FOUND)



"""Single Image Post"""
class UploadProfileImage(APIView):
    def get(self,request):
        matrimonyid=request.GET.get('matrimony_id')
        imageid=request.GET.get('imageid')
        response={}
        if imageid is not None:
           
            image=ProfileMultiImage.objects.get(id=imageid)
                
            return Response({                             
                             "image":image.files.url,
                             "imageid":image.id}
                                ,status=200)
           
       
        elif matrimonyid is not None:
            response={}
            profile=Person.objects.get(matrimony_id=matrimonyid)
            uploadedimage=ProfileMultiImage.objects.filter(profile=profile)
            for i in range(6):
                try:
                    response[i+1]={
                        "imageid":uploadedimage[i].id,
                        "image": uploadedimage[i].files.url

                    }
                except Exception as e:
                    response[i+1]={
                        "imageid":None,
                        "image": None,

                    }
                    
                
                
            
            return Response(response.values())
        else:
            return Response({"message":"somethig wrong check and try latter","status":False},status=200)

        


    def post(self,request):
        if not request.POST._mutable:
            request.POST._mutable=True
       
        matrimonyid=request.GET['matrimony_id']
        profile=Person.objects.filter(matrimony_id=matrimonyid)
        if profile.exists():
           
            image=ProfileMultiImage.objects.create(
                profile=profile[0],\
                files=request.FILES['image'])
           
            return Response({"message":"Profile Image Uploaded",
                             "status":True,
                             "image":image.files.url,
                             "imageid":image.id},status=200)
        else:
            return Response({"message":"Matrimony Id Invalid",
                             "status":False,
                             "matrimony_id":None},status=400)
       

    def delete(self,request):
        
        imageid=request.GET.get('imageid')
        
        
        image=ProfileMultiImage.objects.filter(id=imageid)
        if image.exists():
            image.delete()
            return Response({"message":"Image successfully Deleted","satus":True},status=203)
        else:
            return Response({"message":"Image Id not Found","status":False},status=404)
        


"""NEW MATCH PROFILE"""
class OppositeGenderProfile(APIView):
    def get(self,request):
        matrimonyid=request.GET['matrimony_id']
        person=Person.objects.get(matrimony_id__iexact=matrimonyid)
        query=Q(
           ~ Q(gender=person.gender)
            &
            Q(block=False)
            # &
            # Q(reg_date)
            )
        response={}
        persons=Person.objects.filter(query).order_by('-reg_date')[0:12]
        for person in persons:
            images=ProfileMultiImage.objects.filter(profile__id=person.id)
            response[person.id]={
                "image":images[0].files.url if images.exists() else None,
                "matimony_id":person.matrimony_id,
                "name":person.name
                
                }
        return Response(response.values())
    

"""NEW MATCH JOIN"""
class NewMatchProfile(APIView):
    def get(self,request):
        matrimonyid=request.GET['matrimony_id']
        person=Person.objects.get(matrimony_id__iexact=matrimonyid)
        query=Q(
            ~Q(gender=person.gender)
            &
            Q(block=False)
            #&
            # Q(reg_date)
            )
        response={}
        persons=Person.objects.filter(query).order_by('-reg_date')#[13:]
        for person in persons:
            images=ProfileMultiImage.objects.filter(profile__id=person.id)
            serializer=GenderSerializer(person,many=False).data
            serializer['image']=images[0].files.url if images.exists() else None
            response[person.id]=serializer
            response[person.id].update(height_and_age(person.height,person.dateofbirth))
            response[person.id].update(connect_status(matrimonyid,person.matrimony_id) )
        return Response(response.values())

"""ALL PROFILE """
class AllProfiles(APIView):
    def get(self,request):
        matrimonyid=request.GET['matrimony_id']
        person=Person.objects.get(matrimony_id__iexact=matrimonyid)
        query=Q(
            ~Q(gender=person.gender)
            )
        response={}
        persons=Person.objects.filter(query).order_by('-id')
        for person in persons:
            images=ProfileMultiImage.objects.filter(profile__id=person.id)
            serializer=GenderSerializer(person,many=False).data
            serializer['profileimage']=images[0].files.url if images.exists() else None
            response[person.id]=serializer
            response[person.id].update(height_and_age(person.height,person.dateofbirth))
            response[person.id].update(connect_status(matrimonyid,person.matrimony_id ) )                          
        return Response(response.values())



"""BOOKMARK MATRIMONY ID"""

class BookMarkProfile(APIView):
    def get(self,request) :
        matrimonyid=request.GET['matrimony_id']
        requestid=request.GET['requeted_matrimony_id']
        
        profile=Person.objects.filter(matrimony_id=requestid)
        selfid=Person.objects.get(matrimony_id=matrimonyid)
        
        if profile.exists():
            bookmark=Bookmark.objects.filter(profile=selfid)   
            if bookmark.exists():
                if bookmark[0].album.filter(matrimony_id=requestid).exists():
                    bookmark[0].album.remove(profile[0])
                
                    return Response({"bookmark":False,"status":False})
                else:
                    bookmark[0].album.add(profile[0])
                    return Response({"bookmark":True,"status":True})
                    
            else:
                bookmark=Bookmark.objects.create(profile=selfid)
                bookmark.album.add(profile[0])
                return Response({"bookmark":True,"status":True})
        else:
            return Response({"message":"Requested Matrimony Id Invalid","status":False})

class Album(APIView):
    def get(self,request) :
        matrimonyid=request.GET['matrimony_id']
        bookmark=Bookmark.objects.select_related("profile")\
        .filter(profile__matrimony_id=matrimonyid)   
        if bookmark.exists():
            response={}
            bookmarks=bookmark[0].album.all()
            for person in bookmarks:
                images=ProfileMultiImage.objects.filter(profile__id=person.id)
                response[person.id]={
                    "profileimage":images[0].files.url if images.exists() else None,
                    "matrimony_id":person.matrimony_id
                    }
                                        
            return Response(response.values())
           
                
        else:
            return Response([],status=200)
       
            
        
        
class ProfileMatchPercentage(APIView):
    def get(self,request):
        matrimonyid=request.GET['matrimony_id']
        requestid=request.GET['requeted_matrimony_id']
        
        profile=Person.objects.get(matrimony_id=matrimonyid)
        r_profile=Person.objects.get(matrimony_id=requestid)
        
        r_age=get_age(r_profile.dateofbirth)
        d_age=[i for i in range(25,35)]
        d_height=[
        "4'1''","4'2''","4'3''","4'4''","4'5''","4'6''","4'7''","4'8''","4'9''","4'10''","4'11''","5'0''"  
        "5'1''","5'2''","5'3''","5'4''","5'5''","5'6''","5'7''","5'8''","5'9''","5'10''","5'11''","6'0''"
            
            ]
        response={
            "age":True if int(r_age) in d_age else False,
            "age_range":"25-35" ,
            "height":True if r_profile.height in d_height else False,
            "height_range":"4.5 -5.11",
            'physical_status': True if profile.physical_status==r_profile.physical_status else False,
            "physical_range":"Normal",
            'mother_tongue': True if profile.mother_tongue==r_profile.mother_tongue else False,
            "mother_tongue_range":"Any",
            "marital_status": True if profile.marital_status==r_profile.marital_status else False,
            "marital_range":"Unmarried",
            'drinking_habbit': True if profile.drinking_habbit==r_profile.drinking_habbit else False,
            "drinking_habbit_range":"Any",
            'smoking_habbit': True if profile.smoking_habbit==r_profile.smoking_habbit else False,
            "smoking_habbit_range":"Any",
            'diet_preference': True if profile.diet_preference==r_profile.diet_preference else False,
            "diet_preference_range":"Any",
            'caste': True if profile.caste==r_profile.caste else False,
            "caste_range":"Any",
            'religion': True if profile.religion==r_profile.religion else False,
            "religion_range":"Any",
            'star': True if profile.star==r_profile.star else False,
            "star_range":"Any",
            'occupation': True if profile.occupation==r_profile.occupation else False,
            "occupation_range":"Any",
            "annual_income": True if profile.physical_status==r_profile.physical_status else False,
            "annual_income_range":"3-5",
            'job_sector': True if profile.job_sector==r_profile.job_sector else False,
            "job_sector_range":"Any",
            'city': True if profile.city==r_profile.city else False,
            "city_range":"Any",
            'state': True if profile.state==r_profile.state else False,
            "state_range":"Any",
            'dosham': False,
            "dosham_range":"Any",
            "qualification":True if profile.qualification==r_profile.qualification else False,
            "qualification_range":"Any"
         }  
        
        number_of_true=0
        for key,value in response.items():
            if value is True:
                number_of_true+=1
            else:
                pass
        multi=(number_of_true*100)//18
        response.update({"percentage":multi})
        # list_of_pp=['min_age','max_age','min_height','max_height','physical_status','mother_tongue'
        #             "marital_status",'drinking_habbit',
        #             'smoking_habbit','food','caste','religion','star','occupation'
        #             "annual_income",'job_sector',
        #             'city','state','dosham','religion','star','occupation'
                    
        #             ]
           
    
        return Response(response,status=200)
          

#TESING PHASE ####################
class MatchInPercentage(APIView):
    def get(self,request):
        
        matrimonyid=request.GET['matrimony_id']
        response = {}
        main_user = Person.objects.filter(matrimony_id=matrimonyid).values()
        
        partner_user = Person.objects.filter(~Q(gender=main_user[0]["gender"])).values()

        for index , keys in enumerate(partner_user):
            response[index]={"id":keys['id']}
            # _list=[
            #    'user_id' ,'id','reg_date','reg_update' ,'id','total_access' ,'active_plan','verify' ,'block','gender' ,'phone_number','name' ,'about_myself','matrimony_id','email']
            
            del keys['user_id'], keys['id'],keys['reg_date'],keys['reg_update'],keys['total_access'],keys['active_plan'],keys['verify'],keys['block'],keys['status'],keys['about_myself'],keys['matrimony_id'],keys['email'],keys['gender'],keys['phone_number'] ,keys['name'],keys['image']
            user_full_details= dict(ChainMap(*[{k : True} if partner_user[0][k] == main_user[0][k] else {k:False} for k,v in keys.items()]))
            
            response[index].update(user_full_details)
        matrimonyid=[{"id":value['id'],"count":len([j for i, j in value.items() if j == True])} for key,value in response.items()]
        print(matrimonyid)
        sorted_list=sorted(matrimonyid,key=lambda x:x['count'],reverse=True)
        print(sorted_list)
        list_of_id=[ i['id'] for i in sorted_list]
        
        match_response={}
        persons=Person.objects.filter(id__in=list_of_id)
        
        for person in persons:
            
            images=ProfileMultiImage.objects.filter(profile__id=person.id)
            serializer=GenderSerializer(person,many=False).data
            serializer['profileimage']=images[0].files.url if images.exists() else None
            match_response[person.id]=serializer
            match_response[person.id].update(height_and_age(person.height,person.dateofbirth))
            match_response[person.id].update(connect_status(matrimonyid,person.matrimony_id ) )                          
        return Response(match_response.values())
        

      


class DailyRecomandation(APIView):
    def get(self,request):
        matrimonyid=request.GET['matrimony_id']
        profile=Person.objects.get(matrimony_id=matrimonyid)
        query=Q(
           Q(   ~Q(gender=profile.gender)
                &
                Q(status=True)
            )
           &
           Q(
               Q(physical_status=profile.physical_status)
               |
               Q(mother_tongue=profile.mother_tongue)
               |
               Q(marital_status=profile.marital_status)
               |
               Q(drinking_habbit=profile.drinking_habbit)
               |
               Q(smoking_habbit=profile.smoking_habbit)
               |
               Q(diet_preference=profile.diet_preference)
               |
               Q(caste=profile.caste)
               |
               Q(religion=profile.religion)
               |
               Q(occupation=profile.occupation)
               |
               Q(job_sector=profile.job_sector)
               |
               Q(smoking_habbit=profile.smoking_habbit)
               |
               Q(city=profile.city)
               |
               Q(state=profile.state)
               |
               Q(religion=profile.religion)
               |
               Q(occupation=profile.occupation)
               |
               Q(qualification=profile.qualification)

           ) 
           
            
        )
        
        response={}
        r_profile=Person.objects.filter(query).order_by('-reg_date')
        for r_pro in r_profile:
            images=ProfileMultiImage.objects.filter(profile=r_pro)
            response[r_pro.id]={
                "matrimony_id":r_pro.matrimony_id,
                "image":images[0].files.url if images.exists() else None,
                "height":height(r_pro.height),
                "age":get_age(r_pro.dateofbirth),
                "gender":r_pro.gender,
                "name":r_pro.name,
                "phone_number":r_pro.phone_number
                
            }
            response[r_pro.id].update(connect_status(matrimonyid,r_pro.matrimony_id))
        
        return Response(response.values(),status=200)
    
    


"""SHFFLEING PROFILE SHOWING OPPISITE GENDER PROFILE"""
class NeedToUpdateFields(APIView):
    def get(self,request):
        response={}
        matrimonyid=request.GET['matrimony_id']
        
        profile=Person.objects.get(matrimony_id=matrimonyid)
        
        _list=['horoscope',"habbits",'workplace','star',
               "total_family_members",'college' ,"annual_income"]
        
        
        for info in _list:
            if getattr(profile,info)=="" or getattr(profile,info) is None :
                
                response[info]={ 
                                "name":info,
                                "about":"Get 90 imes more boostup your profile"
                                }                             
            else:
                pass                   
            images=ProfileMultiImage.objects.filter(profile__matrimony_id=matrimonyid)
            if images.exists()==False:
                response['image']={
                "name":"image",
                "about":"Get 90 imes more boostup your profile"
                }                     
        return Response(response.values())
    


"""Explore"""
class Explore(APIView):
    def get(self,request):
        
        matrimonyid=request.GET['matrimony_id']
        
        profile=Person.objects.get(matrimony_id=matrimonyid)
        
        profile=Person.objects.aggregate(
            star=Count('pk', filter=Q(
                Q(star=profile.star)& ~Q(gender=profile.gender)
                )),
            occupation=Count('pk', filter=Q(
                
                Q(occupation=profile.occupation)& ~Q(gender=profile.gender)
                )),
            qualification=Count('pk', filter=Q(
                
                Q(qualification=profile.qualification)& ~Q(gender=profile.gender)
                )),
            
            horoscope=Count('pk', filter=Q(
                
                Q(horoscope=profile.horoscope)& ~Q(gender=profile.gender)
                )),
           
            city=Count('pk', filter=Q(
                
                Q(city=profile.city)& ~Q(gender=profile.gender)
                )),
            state=Count('pk', filter=Q(
                
                Q(state=profile.state)& ~Q(gender=profile.gender)
                )),
            
            workplace=Count('pk', filter=Q(
                
                Q(workplace=profile.workplace)& ~Q(gender=profile.gender)
                )),
        
        )   
        response={}
        for key,value in profile.items():
            banner=BannerImage.objects.filter(name=key,status=True)
            response[key]={
                "name":key,
                "image":banner[0].image.url if banner.exists() else None,
                "color":banner[0].background if banner.exists() else None,
                "count":value
            }            
        return Response(response.values())
    

"""EXPLORE PART"""
class ExploreProfile(APIView):
    def get(self,request):
        matrimonyid=request.GET['matrimony_id']
        _q=request.GET['q']
        
        profile=Person.objects.get(matrimony_id=matrimonyid) 
        _list=['star','occupation','workplace','state','city','horoscope','qualification']
        if _q not in _list:
        
            return Response({"message":"Invalid query",'status':False},status=400)
        elif _q=="state":
        
            query=Q(~Q(gender=profile.gender)& Q(state=getattr(profile,_q)) )
        elif _q=="star":     
            query=Q(~Q(gender=profile.gender)& Q(star=getattr(profile,_q)) )
        elif _q=="occupation":
            query=Q(~Q(gender=profile.gender)& Q(occupation=getattr(profile,_q)) )     
        elif _q=="workplace":
            query=Q(~Q(gender=profile.gender)& Q(workplace=getattr(profile,_q)) )
        elif _q=="city":
            query=Q(~Q(gender=profile.gender)& Q(city=getattr(profile,_q)) )
        elif _q=="horoscope":
            query=Q(~Q(gender=profile.gender)& Q(horoscope=getattr(profile,_q)) )
        elif _q=="qualification":
            query=Q(~Q(gender=profile.gender)& Q(qualification=getattr(profile,_q)) )
    
           
            
       
        matches=Person.objects.filter(query).order_by('-id')  
        if matches.exists():
            response={}
            for match in matches:
                images=ProfileMultiImage.objects.filter(profile__id=match.id)
                #bookmark
                bookmark=Bookmark.objects.filter(profile=profile,album__matrimony_id=match.matrimony_id)
                serializers=GenderSerializer(match,many=False).data
                serializers['profileimage']=images[0].files.url if images.exists() else None
                serializers['bookmark']= True if bookmark.exists() else False
                serializers.update(height_and_age(match.height,match.dateofbirth))
                serializers.update(connect_status(matrimonyid,match.matrimony_id))
                response[match.id]=serializers
            return Response(response.values())
        else:
            return Response([],status=400)
 
 
 
"""GET VIEWED PROFILE"""

"""PROFILE I SAW  PROFILE """
class ISawProfile(APIView):
    def get(self,request):
        matrimonyid=request.GET['matrimony_id']
        query=request.GET['q']#saw,viewed
        
        if query != "saw":
            return Response({"message":"Invalid query","status":False},status=200)
        
        profile=Person.objects.get(matrimony_id__iexact=matrimonyid)
        
        
        
        view_profile=ViewedProfile.objects.filter(profile=profile)
        # if view_profile.exists()==False:
        #     return Response([],status=200)
        
        response={}
        for view in view_profile[0].view.all():
            images=ProfileMultiImage.objects.filter(profile__id=view.id)
            serializer=GenderSerializer(view,many=False).data
            serializer['profileimage']=images[0].files.url if images.exists() else None
            serializer.update(height_and_age(view.height,view.dateofbirth))
            serializer.update(connect_status(matrimonyid,view.matrimony_id))
            response[view.id]=serializer
        return Response(response.values())
    
    
"""PROFILE  WHO VIEWED MY PROFILE """
class WhoSawMyProfile(APIView):
    def get(self,request):
        matrimonyid=request.GET['matrimony_id']
        query=request.GET['q']#saw,viewed
        
        if query!="viewed":
            return Response({"message":"Invalid query","status":False},status=200)
        
        person=Person.objects.get(matrimony_id__iexact=matrimonyid)
        
        filter_query=Q(view__id=person.id)
        view_profile=ViewedProfile.objects.filter(filter_query)
        if view_profile.exists()==False:
            return Response([],status=200)
        
        response={}
        for view in view_profile:
            images=ProfileMultiImage.objects.filter(profile__id=view.profile.id)
            serializer=GenderSerializer(view.profile,many=False).data
            serializer['profileimage']=images[0].files.url if images.exists() else None
            serializer.update(height_and_age(view.height,view.dateofbirth))
            serializer.update(connect_status(matrimonyid,view.matrimony_id))
            response[view.id]=serializer
        return Response(response.values())




#######################FRIEND REQUEST SEND#########################    
"""SEND FRIEND REQUEST"""   
class SendFriendRequest(APIView):
    def get(self,request):
        matrimonyid=request.GET['matrimony_id']
        requestid=request.GET['requeted_matrimony_id']
        query=Q(
            profile__matrimony_id=matrimonyid,
            requested_matrimony_id=requestid,
            
        )
        send_friend_request=FriendRequests.objects.filter(query)
        if send_friend_request.exists():
            return Response({"message":"Request Exsits","connect_status":send_friend_request[0].request_status})  
        else:
            profile=get_object_or_404(Person,matrimony_id=matrimonyid)
            get_object_or_404(Person,matrimony_id=requestid)
            FriendRequests.objects.create(profile=profile,requested_matrimony_id=requestid)
            return Response({"message":"Request Send Successfully","connect_status":"Waiting"},status=200)
    
    def post(self,request):
        records=FriendRequests.objects.all().order_by('-created_date')
        response={}
        for re in records:
            response[re.id]={
                "profile":re.profile.matrimony_id,
                "requested_matrimony_id":re.requested_matrimony_id,
                "request_status":re.request_status,
                "status":re.status,
                "create":re.created_date
            }
        return Response(response.values())    
    def put(self,request):
        if not request.POST._mutable:
            request.POST._mutable=True
        data=request.data
        connectid=request.GET['connectid']
        _list=("Connected","Rejected")
        if data['request_status'] not in _list:
            return Response({"message":"Invalid Choice","status":False},status=400)
        
        
        get_request=FriendRequests.objects.get(id=connectid)
        get_request.request_status=data['request_status']
        get_request.save()
        return Response({"connect_staus":get_request.request_status})
    
    def delete(self,request):
        connectid=request.GET['connectid']
        fr=FriendRequests.objects.filter(id=connectid)
        if fr.exists():
            fr.delete()
            return Response({"message":"deleted"})
        else:
            return Response({"message":"no found"})
           
    
"""WAITING,RECEIVED,REJECTED FRIEND REQUEST DATA"""  
class StautsOfSendRequest(APIView):
    def get(self,request):
        matrimonyid=request.GET['matrimony_id']
        request_query=request.GET['q']
        _list=("Connected","Rejected",'Waiting')
        
        if request_query not in _list:
            return Response({"message":"Invalid query","status":False},status=400)
        
        query=Q(
            Q(request_status=request_query,requested_matrimony_id=matrimonyid)
            |
            Q(request_status=request_query,profile__matrimony_id=matrimonyid)
        )
        send_friend_request=FriendRequests.objects.filter(query).order_by("-created_date")
        
        if send_friend_request.exists()==False:
            return Response([],status=200)
        response={}
        for view in send_friend_request:
            # print("+++++++++++++++++++")
            # print(matrimonyid,view.profile.matrimony_id,view.requested_matrimony_id)
            #print("xxxxxxxxxxxxxxxxxxxxxxxxx")
            if matrimonyid==view.profile.matrimony_id:
                # print("xxxxxxxxxxxif ")
                image_query=Q(profile__matrimony_id=view.requested_matrimony_id)
                instance=get_object_or_404(Person,matrimony_id=view.requested_matrimony_id)
            else:
                # print("xxxxxxxxxxxelsse ")
                image_query=Q(profile__matrimony_id=view.profile.matrimony_id) 
                instance=get_object_or_404(Person,matrimony_id=view.profile.matrimony_id) 
            images=ProfileMultiImage.objects.filter(image_query)
                        
            serializer=GenderSerializer(instance,many=False).data
            serializer['profileimage']=images[0].files.url if images.exists() else None
            serializer['connect_status']=view.request_status
            serializer['connectid']=view.id
            serializer['created_date']=view.created_date.strftime("%Y-%b-%d")
            serializer['updated_date']=view.updated_date.strftime("%Y-%b-%d")
            serializer.update(height_and_age(instance.height,instance.dateofbirth))
            response[view.id]=serializer
        return Response(response.values())



"""CHECK FRIEND REQUEST STATUS CONNECTED,REJECTED,WAITING"""  
class GETSendedFriendRequest(APIView):
    def get(self,request):
        matrimonyid=request.GET['matrimony_id']
        request_query=request.GET['q']
        _list=('send_request',)
        if request_query not in _list:
            return Response({"message":"Invalid query","status":False},status=400)
        
        query=Q(
            profile__matrimony_id=matrimonyid,
            
            )
        
        send_friend_request=FriendRequests.objects.filter(query)
        if send_friend_request.exists()==False:
            return Response([],status=200)
        
        response={}
        for view in send_friend_request:
            images=ProfileMultiImage.objects.filter(profile__matrimony_id=view.requested_matrimony_id)
            profileid=get_object_or_404(Person,matrimony_id=view.requested_matrimony_id)
            serializer=GenderSerializer(profileid,many=False).data
            serializer['profileimage']=images[0].files.url if images.exists() else None
            serializer['connect_status']=view.request_status
            serializer.update(height_and_age(profileid.height,profileid.dateofbirth))
            serializer['created_date']=view.created_date.strftime("%Y-%b-%d")
            serializer['updated_date']=view.updated_date.strftime("%Y-%b-%d")
           
            response[view.id]=serializer
        return Response(response.values())


######################FINISH####################################


