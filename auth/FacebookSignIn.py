from OAuthAll import OAuthSignIn

class FacebookSignIn(OAuthSignIn):
	def __init__(self,app):
		super(FacebookSignIn,self).__init__('facebook',app)
		self.service = OAuth2Service(name='facebook',
			cliend_id=self.consumer_id,
			authorise_url = 'https://graph.facebook.com/oauth/authorize',
			access_token_url='https://graph.facebook.com/oauth/access_token',
			base_url = 'https://graph.facebook.com/'
			)
	def authorise(self,app):
		return redirect(self.service.get_authorize_url(scope='email', response_type='code',redirect_uri = self.get_callback_url()))

	def callback(self):
		if 'code' not in request.args:
			return None, None, None
		oauth_session = self.service.get_auth_session(
			data={
			'code:': request.args['code']
			'grant_type':'authrization_code',
			'redirect_uri': self.get_callback_url()}
			)
		me = oauth_session.get('me').json()
        return (
            'facebook$' + me['id'],
            me.get('email').split('@')[0],
            me.get('email')
        )