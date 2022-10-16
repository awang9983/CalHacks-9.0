import requests
import json
import datetime
import keyring
import logging
from collections import defaultdict
import inspect
from logging import log
from .. import Base
from sqlalchemy import BigInteger, Column, String, Integer, Float, DateTime, TIMESTAMP, func
from pls import Strava
from requests import session
from Activity import Strava_Activity

###credit to Fernando Rodriguez for foundation of interacting with Strava API

log=logging.getLogger()

class Strava():
    def __init__(self):
        self.storage='creds.txt'
        try:
            with open(self.storage,'r') as f:
                datastore=json.load(f)
        except IOError:
            log.warning("Credentials do not exist, need to creade creds.txt")
            exit()
        # Probably should be here, at least use keyring instead
        self._client_id=keyring.get_password('Strava','client_id')
        self._client_secret=keyring.get_password('Strava','client_secret')
        self.access_token=datastore['access_token']
        self.expires_at=datastore['expires_at']
        self.expires_in=datastore['expires_in']
        self.refresh_token=datastore['refresh_token']
        self.goal=0
        self.wallet=0
        self.bet=0
        self.deadline=datetime.datetime.utcnow().timestamp()

        self.set_access_token()

    def set_access_token(self):
        if self.valid_token():
            self.access_token=self.access_token
        else:
            token_str=self.refresh()
            token_json=token_str.json()
            log.info('New Credentials Obtained',token_json)
            self.store_creds(token_json)
            try:
                self.access_token=token_json['access_token']
                self.expires_in=token_json['expires_in']
            except:
                log.warning("Could not set new token values")
                exit()

    def valid_token(self):
        if self.expires_at>=datetime.datetime.utcnow().timestamp():
            return True
        else:
            return False

    def refresh(self):
        log.info('Trying to Refresh Token')
        refresh_base_url="https://www.strava.com/api/v3/oauth/token"
        refresh_url=refresh_base_url+\
        '?client_id='+self._client_id+\
        '&client_secret='+self._client_secret+\
        '&grant_type=refresh_token'+\
        '&refresh_token='+self.refresh_token
        r=requests.post(refresh_url)
        if r.status_code==200:
            return r
        else:
            log.critical('Could not refresh token')
            exit()
    
    def set_goal(x):
        goal=x

    def checker(self):
        if (self.deadline > datetime.datetime.utcnow.timestampe()):
            return
        else: ##r is api pull from the thing
            if (Strava_Activity.distance > self.goal):
                self.wallet += self.bet
                self.bet=0
            else:
                self.wallet -= self.bet
                self.bet=0
    
    def store_creds(self,r):
        print('JSON',r)
        if len(r) > 0:
            try:
                with open(self.storage,'w') as outfile:
                    json.dump(r,outfile)
            except:
                log.warning("Issue with credentials")
        else:
            log.warning("No Response to Token Storage")

    def get_activities(self, before='',after='',page=1,per_page=30):
        api_call_headers = {'Authorization': 'Bearer ' + self.access_token}
        activities_url="https://www.strava.com/api/v3/athlete/activities?"
        try:
            if self.valid_token():
                r=requests.get(activities_url, headers=api_call_headers, verify=False)
            else:
                self.refresh()
                r=requests.get(activities_url, headers=api_call_headers, verify=False)
            if r.status_code==200:
                log.info('Activities obtained')
                return r
            else:
                log.warning('Could not get activities')
                return r
        except:
            log.critical('Something went wrong')
            return('API Problem')

if __name__=="__main__":
    strv=Strava()
    print(strv.access_token)
    print(json.dumps(strv.get_activities().json(), indent=4, sort_keys=True))


class Strava_Activity(Base):
    __tablename__='strava_activity'
    #index=Column(Integer(), primary_key=True)
    id=Column(BigInteger(), primary_key=True)
    owner=Column(Integer())#Probs Foregin keyring
    activity_type=Column(String(50))
    distance=Column(Float())
    elapsed_time=Column(Float())
    average_speed=Column(Float())
    average_cadence=Column(Float())
    average_heartrate=Column(Float())
    name=Column(String(50))
    utc_offset=Column(Float())
    max_speed=Column(Float())
    max_heartrate=Column(Float())
    total_elevation_gain=Column(Float())
    upload_id=Column(BigInteger())
    moving_time=Column(Float())
    start_date=Column(DateTime())
    start_date_local=Column(DateTime())
    last_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())

    def __repr__(self):
        return "<STRAVA ACTIVITY '%s', distance='%s', type='%s', date='%s'>"%(self.id, self.distance, self.activity_type, self.start_date_local)

    def Update_Strava_Activities():
        # Initialize Strava connection and get the data
        stv=Strava()
        data=stv.get_activities().json()

        # Get the required columns from our Strava Class
        strava_params=[c for c in inspect(Strava_Activity).columns.keys()]

        # Remove the last time parameter as that is autogenerated
        strava_params.remove('last_time')

        #We will first create all our model class instances for Strava_Activity
        acts=[]
        for dic in data:
            #Initialize an empty default dict so we dont get triped up with key missing issues
            d = defaultdict(lambda: None, dic)
            #Rename some columns from the API json so they match our class
            d['owner']=d['athlete']['id']
            d['activity_type']=d['type']

            #Search for values needed in our class in the API json
            update={}
            for val in strava_params:
                update[val]=d[val]

            log.info(update)

            #Initialize our model class from the dictionary
            act=Strava_Activity(**update)
            acts.append(act)

        # Merge our results into the database (I will rewrite all of them for the last 30 items regardless of what it says), at the current moment I don't need to check the API for deleted activities but might in the future.
        for act in acts:
            try:
                with session.begin_nested():
                    session.merge(act)
                log.info("Updated: %s"%str(act))
            except:
                log.info("Skipped %s"%str(act))
        session.commit()
        session.flush()

