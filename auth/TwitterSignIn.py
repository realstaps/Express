from OAuthAll import OAuthSignIn

class TwitterSignIn(OAuthSignIn):
	def __init__(self,app):
		super(TwitterSignIn,self).__init__('twitter',app)

		self.service = OAuth1Service(
			name = 'twitter',
			consumer_key = self.consumer_key,
			consumer_secret = self.consumer_secret,
			request_token_url='https://api.twitter.com/oauth/request_token',
            authorize_url='https://api.twitter.com/oauth/authorize',
            access_token_url='https://api.twitter.com/oauth/access_token',
            base_url='https://api.twitter.com/1.1/'
			)
	def authorise(self):

		request_token = self.service.get_request_token(
			params={'oauth_callback':self.get_callback_url()}
			)

		session['request_token'] = request_token
		return redirect(self.service.get_authorise_url(request_token[0]))
	def callback(self):
        request_token = session.pop('request_token')
        if 'oauth_verifier' not in request.args:
            return None, None, None
        oauth_session = self.service.get_auth_session(
            request_token[0],
            request_token[1],
            data={'oauth_verifier': request.args['oauth_verifier']}
        )
        me = oauth_session.get('account/verify_credentials.json').json()
        social_id = 'twitter$' + str(me.get('id'))
        username = me.get('screen_name')
        return social_id, username, None 


	