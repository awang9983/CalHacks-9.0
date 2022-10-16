from .. import db
class Strava_Activity(db.Model):
    __tablename__='strava_activity'
    #index=db.Column(Integer(), primary_key=True)
    id=db.Column(db.BigInteger(), primary_key=True)
    owner=db.Column(db.Integer())#Probs Foregin keyring
    activity_type=db.Column(db.String(50))
    distance=db.Column(db.Float())
    elapsed_time=db.Column(db.Float())
    average_speed=db.Column(db.Float())
    average_cadence=db.Column(db.Float())
    average_heartrate=db.Column(db.Float())
    name=db.Column(db.String(50))
    utc_offset=db.Column(db.Float())
    max_speed=db.Column(db.Float())
    max_heartrate=db.Column(db.Float())
    total_elevation_gain=db.Column(db.Float())
    upload_id=db.Column(db.BigInteger())
    moving_time=db.Column(db.Float())
    start_date=db.Column(db.DateTime())
    start_date_local=db.Column(db.DateTime())
    last_time = db.Column(db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.current_timestamp())

    @property
    def as_json(self):
       #Return object data in easily serializable format
       return {
    'index':self.id,
    'speed':self.average_speed,
    'cadence':self.average_cadence,
    'heartrate':self.average_heartrate,
    'distance':self.distance,
    'moving_time':self.moving_time,
    'date':self.start_date_local.strftime('%Y-%m-%d')}

    def __repr__(self):
        return "<STRAVA ACTIVITY '%s', distance='%s', type='%s', date='%s'>"%(self.id, self.distance, self.activity_type, self.start_date_local)
