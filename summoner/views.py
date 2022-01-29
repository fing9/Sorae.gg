from aifc import Error
from tkinter.ttk import Entry
import django
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import TierSerializer, UserSerializer, GameRecordSerializer
from summoner.models import Tier, GameRecord, User, UpdateDB
from riotapi.SummonerData import SummonerAPI
from django.core.exceptions import ObjectDoesNotExist
from config.settings import STATIC_URL

def index(request):
    return render(request, 'summoner/index.html')

def search(request):
    summonerName = request.GET['userName']

    summoner = SummonerAPI(summonerName)

    if not summoner.isValid() :
        return render(request, 'summoner/summoner_info.html', {'userName': summonerName,'isValid':False})
    
    tier = summoner.getTier()

    record = summoner.getTotalRecord(0,10)

    user = summoner.getUser()

    info = {'userName': summonerName, 'user':user, 'tier':tier, 'record': record, 'isValid':True, 'STATIC_URL':STATIC_URL}

    return render(request,'summoner/summoner_info.html', info)


class SummonerView(APIView):

    def get(self, request):

        # URL : sorae.gg/api?userName
        summonerName = request.GET['userName']
        summoner = SummonerAPI(summonerName)
        summonerName = summoner.getName()

        if not summoner.isValid() :
            return render(request, 'summoner/summoner_info.html', {'userName':summonerName})
        
        # DB 조회
        try:
            userQuery = User.objects.get(summoner_name=summonerName)
        except ObjectDoesNotExist:
            """
            if Data dosen't exist then create DB
            """
            # Data 생성
            tierData = summoner.getTier()
            gameRecordData = summoner.getTotalRecord(0, 10)
            userData = summoner.getUser()

            # DB 저장
            DB = UpdateDB(summoner)

            DB.createUser(userData)
            DB.createTier(tierData)
            for record in reversed(gameRecordData):
                DB.createGameRecord(record)
                DB.createDetailRecord(record)
          

        # serializer
        userQuery = User.objects.get(summoner_name=summonerName)
        tierQuery = Tier.objects.get(summoner_name=summonerName)
        recordQuery = GameRecord.objects.filter(summoner_name=summonerName)
        userSerialize = UserSerializer(userQuery)
        tierSerialize = TierSerializer(tierQuery)
        gameRecordSerialize = GameRecordSerializer(recordQuery, many=True)

        return render(request, 'summoner/summoner_info.html', {'user':userSerialize.data, 'tier':tierSerialize.data, 'gameRecord':gameRecordSerialize.data\
            ,'STATIC_URL':STATIC_URL})

class MainView(APIView):

    def post(self, request):

        summonerName = request.data['userName']

        API = SummonerAPI(summonerName)

        if API.isValid():
            # API
            tierData = API.getTier()
            gameRecordData = API.getTotalRecord(0, 10)
            userData = API.getUser()

            # DB 저장

            DB = UpdateDB(summonerName)

            DB.createUser(userData)
            DB.createTier(tierData)
            for record in reversed(gameRecordData):
                DB.createGameRecord(record)
                DB.createDetailRecord(record)

            # DB.deleteGameRecord(summonerName)
            return Response(data={'status': 200})
        else:
            return Response(data={'status': 404})


if __name__ == "__main__":
    user = SummonerAPI("민스님")
    DB = UpdateDB("민스님")
    DB.deleteGameRecord("민스님")
    print(user.getTier())