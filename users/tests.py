from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class UserAuthTests(TestCase):
	def setUp(self):
		self.User = get_user_model()

	def test_register_creates_user(self):
		url = reverse('register')
		data = {
			'username': 'testuser',
			'email': 'test@example.com',
			'full_name': 'Test User',
			'role': 'voter',
			'password1': 'safe-password-123',
			'password2': 'safe-password-123',
		}
		resp = self.client.post(url, data)
		# should redirect to login
		self.assertEqual(resp.status_code, 302)
		self.assertTrue(self.User.objects.filter(username='testuser').exists())
		user = self.User.objects.get(username='testuser')
		self.assertEqual(user.email, 'test@example.com')
		self.assertEqual(user.full_name, 'Test User')

	def test_login_view(self):
		# create a user then login via view
		user = self.User.objects.create_user(username='loginuser', email='login@example.com', password='p@ssword')
		url = reverse('login')
		resp = self.client.post(url, {'username': 'loginuser', 'password': 'p@ssword'})
		# login should redirect to home page hub
		self.assertEqual(resp.status_code, 302)
		# follow redirect and ensure we land on the home view
		follow = self.client.get(resp.url)
		self.assertContains(follow, 'Online Voting System')

	def test_logout_clears_session(self):
		user = self.User.objects.create_user(username='logoutuser', email='logout@example.com', password='p@ssword')
		self.client.login(username='logoutuser', password='p@ssword')
		resp = self.client.get(reverse('logout'))
		# after logout we expect to be redirected to home
		self.assertEqual(resp.status_code, 302)
		follow = self.client.get(resp.url)
		self.assertContains(follow, 'Online Voting System')

	def create_admin(self):
		return self.User.objects.create_user(username='adminuser', email='admin@example.com', password='adminpass', role='admin', is_staff=True)

	def test_admin_party_crud(self):
		# admin can create, edit, delete party
		admin = self.create_admin()
		self.client.login(username='adminuser', password='adminpass')
		# create
		resp = self.client.post(reverse('party_add'), {'name': 'Alpha Party'})
		self.assertEqual(resp.status_code, 302)
		from .models import Party, Candidate
		self.assertTrue(Party.objects.filter(name='Alpha Party').exists())

		party = Party.objects.get(name='Alpha Party')
		# edit
		resp = self.client.post(reverse('party_edit', args=[party.pk]), {'name': 'Alpha Party Updated'})
		self.assertEqual(resp.status_code, 302)
		party.refresh_from_db()
		self.assertEqual(party.name, 'Alpha Party Updated')

		# delete
		resp = self.client.post(reverse('party_delete', args=[party.pk]))
		self.assertEqual(resp.status_code, 302)
		self.assertFalse(Party.objects.filter(pk=party.pk).exists())

	def test_non_admin_cannot_access_management(self):
		# a regular voter cannot access admin management pages
		user = self.User.objects.create_user(username='normal', email='normal@example.com', password='pw', role='voter')
		self.client.login(username='normal', password='pw')
		resp = self.client.get(reverse('party_list'))
		# Should redirect away (decorator sends to users_home)
		self.assertEqual(resp.status_code, 302)

	def test_admin_can_create_candidate(self):
		admin = self.create_admin()
		self.client.login(username='adminuser', password='adminpass')
		from .models import Party, Candidate
		party = Party.objects.create(name='Beta Party')
		resp = self.client.post(reverse('candidate_add'), {'name': 'Alice', 'age': '35', 'party': party.pk, 'area': 'North'})
		self.assertEqual(resp.status_code, 302)
		self.assertTrue(Candidate.objects.filter(name='Alice', party=party).exists())

	def test_candidate_user_link_and_audit(self):
		# ensure candidate can be linked to a user and audit log is created
		admin = self.create_admin()
		self.client.login(username='adminuser', password='adminpass')
		from .models import Party, Candidate
		party = Party.objects.create(name='Gamma')
		user = self.User.objects.create_user(username='candidateuser', email='cand@example.com', password='pw', role='candidate')
		candidate = Candidate.objects.create(name='Candidate One', age=40, party=party, area='East', user=user)
		# ensure link
		self.assertEqual(candidate.user, user)
		# check audit record created
		from audit.models import AuditLog
		self.assertTrue(AuditLog.objects.filter(target_model='users.Candidate', target_repr__contains='Candidate One').exists())

	def test_election_and_results(self):
		admin = self.create_admin()
		self.client.login(username='adminuser', password='adminpass')
		from elections.models import Election
		from .models import Vote, Candidate, Party
		from django.utils import timezone
		start = timezone.now()
		end = timezone.now()
		e = Election.objects.create(title='Test Election', election_type='single', start_date=start, end_date=end, is_active=True)
		party = Party.objects.create(name='Electoral Party')
		c1 = Candidate.objects.create(name='Cand A', age=40, party=party, area='North', is_approved=True)
		c2 = Candidate.objects.create(name='Cand B', age=38, party=party, area='South', is_approved=True)
		# assign to election
		c1.elections.add(e)
		c2.elections.add(e)

		# create voters and votes
		v1 = self.User.objects.create_user(username='v1', email='v1@example.com', password='pw', role='voter')
		v2 = self.User.objects.create_user(username='v2', email='v2@example.com', password='pw', role='voter')
		from .models import Voter
		vobj1 = Voter.objects.create(user=v1, voter_id='V1', mobile='123', address='addr')
		vobj2 = Voter.objects.create(user=v2, voter_id='V2', mobile='456', address='addr2')
		Vote.objects.create(voter=vobj1, candidate=c1, election=e)
		Vote.objects.create(voter=vobj2, candidate=c2, election=e)

		# access results overview and per-election
		resp = self.client.get(reverse('results_overview'))
		self.assertEqual(resp.status_code, 200)

		resp = self.client.get(reverse('results_for_election', args=[e.pk]))
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, 'Cand A')

	def test_admin_pages_render(self):
		# admin should be able to open each management page
		admin = self.create_admin()
		self.client.login(username='adminuser', password='adminpass')
		pages = [
			reverse('user_list'),
			reverse('party_list'),
			reverse('candidate_list'),
			reverse('election_list'),
			reverse('audit_list'),
			reverse('backups_list'),
			reverse('results_overview'),
		]
		for p in pages:
			resp = self.client.get(p)
			self.assertEqual(resp.status_code, 200, msg=f'Failed to open {p}')

	def test_root_redirect_behaviour(self):
		# unauthenticated -> root should go to login
		resp = self.client.get('/')
		self.assertEqual(resp.status_code, 302)
		self.assertIn(reverse('login'), resp.url)

		# login then root should go to users_home
		user = self.User.objects.create_user(username='someuser', email='some@example.com', password='pw')
		self.client.login(username='someuser', password='pw')
		resp = self.client.get('/')
		self.assertEqual(resp.status_code, 302)
		self.assertIn(reverse('users_home'), resp.url)

	def test_logged_in_cannot_view_login_page(self):
		user = self.User.objects.create_user(username='someuser2', email='some2@example.com', password='pw')
		self.client.login(username='someuser2', password='pw')
		resp = self.client.get(reverse('login'))
		self.assertEqual(resp.status_code, 302)
		self.assertIn(reverse('users_home'), resp.url)

	def test_logged_in_cannot_view_register_page(self):
		user = self.User.objects.create_user(username='someuser3', email='some3@example.com', password='pw')
		self.client.login(username='someuser3', password='pw')
		resp = self.client.get(reverse('register'))
		self.assertEqual(resp.status_code, 302)
		self.assertIn(reverse('users_home'), resp.url)

	def test_home_shows_dashboard_nav(self):
		resp = self.client.get(reverse('users_home'))
		self.assertEqual(resp.status_code, 200)
		# quick nav should be present
		self.assertContains(resp, 'Admin Dashboard')


# --- VOTER WORKFLOW TESTS ---

class VoterWorkflowTests(TestCase):
	def setUp(self):
		self.User = get_user_model()
		from .models import Voter, Notification, Vote
		from elections.models import Election
		from django.utils import timezone
		
		# Create a voter user
		self.voter_user = self.User.objects.create_user(
			username='voteruser',
			email='voter@example.com',
			password='voterpass',
			role='voter'
		)
		
		# Create party and candidate
		from .models import Party, Candidate
		self.party = Party.objects.create(name='Test Party')
		self.candidate = Candidate.objects.create(
			name='Test Candidate',
			age=35,
			party=self.party,
			area='Area A',
			is_approved=True
		)
		
		# Create election
		now = timezone.now()
		self.election = Election.objects.create(
			title='Test Election',
			election_type='single',
			start_date=now,
			end_date=now + timezone.timedelta(days=1),
			is_active=True
		)
		self.election.candidates.add(self.candidate)

	def test_voter_can_register(self):
		"""Test voter can complete voter registration."""
		self.client.login(username='voteruser', password='voterpass')
		
		url = reverse('voter_register')
		data = {
			'voter_id': 'V001',
			'mobile': '1234567890',
			'address': '123 Main St'
		}
		resp = self.client.post(url, data)
		self.assertEqual(resp.status_code, 302)
		
		from .models import Voter
		self.assertTrue(Voter.objects.filter(user=self.voter_user).exists())
		voter = Voter.objects.get(user=self.voter_user)
		self.assertEqual(voter.voter_id, 'V001')
		self.assertEqual(voter.verification_status, 'pending')

	def test_voter_registration_creates_notification(self):
		"""Test that registration creates a notification."""
		self.client.login(username='voteruser', password='voterpass')
		
		url = reverse('voter_register')
		data = {
			'voter_id': 'V002',
			'mobile': '1234567890',
			'address': '456 Oak St'
		}
		self.client.post(url, data)
		
		from .models import Voter, Notification
		voter = Voter.objects.get(user=self.voter_user)
		self.assertTrue(Notification.objects.filter(voter=voter).exists())
		notif = Notification.objects.get(voter=voter)
		self.assertEqual(notif.notification_type, 'registration')

	def test_unverified_voter_cannot_vote(self):
		"""Test that unverified voters cannot cast votes."""
		from .models import Voter
		voter = Voter.objects.create(
			user=self.voter_user,
			voter_id='V003',
			mobile='9876543210',
			address='789 Elm St',
			is_verified=False
		)
		
		self.client.login(username='voteruser', password='voterpass')
		url = reverse('voter_cast_vote', args=[self.election.id])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 302)

	def test_verified_voter_can_access_voting(self):
		"""Test that verified voters can access voting page."""
		from .models import Voter
		voter = Voter.objects.create(
			user=self.voter_user,
			voter_id='V004',
			mobile='5555555555',
			address='321 Pine St',
			is_verified=True,
			verification_status='verified'
		)
		
		self.client.login(username='voteruser', password='voterpass')
		url = reverse('voter_cast_vote', args=[self.election.id])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, 'Test Candidate')

	def test_voter_cast_vote(self):
		"""Test voter can successfully cast a vote."""
		from .models import Voter, Vote
		voter = Voter.objects.create(
			user=self.voter_user,
			voter_id='V005',
			mobile='6666666666',
			address='654 Birch St',
			is_verified=True,
			verification_status='verified'
		)
		
		self.client.login(username='voteruser', password='voterpass')
		url = reverse('voter_cast_vote', args=[self.election.id])
		data = {'candidate_id': self.candidate.id}
		resp = self.client.post(url, data)
		self.assertEqual(resp.status_code, 302)
		
		# Check vote was recorded
		self.assertTrue(Vote.objects.filter(voter=voter, candidate=self.candidate, election=self.election).exists())

	def test_voter_cannot_vote_twice_in_same_election(self):
		"""Test one-vote-per-election constraint."""
		from .models import Voter, Vote
		voter = Voter.objects.create(
			user=self.voter_user,
			voter_id='V006',
			mobile='7777777777',
			address='987 Walnut St',
			is_verified=True,
			verification_status='verified'
		)
		
		# Cast first vote
		Vote.objects.create(voter=voter, candidate=self.candidate, election=self.election)
		
		# Try to cast second vote
		self.client.login(username='voteruser', password='voterpass')
		url = reverse('voter_cast_vote', args=[self.election.id])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 302)

	def test_voter_vote_confirmation_page(self):
		"""Test voter can see vote confirmation page."""
		from .models import Voter, Vote
		voter = Voter.objects.create(
			user=self.voter_user,
			voter_id='V007',
			mobile='8888888888',
			address='147 Ash St',
			is_verified=True,
			verification_status='verified'
		)
		
		vote = Vote.objects.create(voter=voter, candidate=self.candidate, election=self.election)
		
		self.client.login(username='voteruser', password='voterpass')
		url = reverse('voter_vote_confirmation', args=[self.election.id])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, 'Test Candidate')

	def test_voter_profile_page(self):
		"""Test voter can view profile page."""
		from .models import Voter
		voter = Voter.objects.create(
			user=self.voter_user,
			voter_id='V008',
			mobile='9999999999',
			address='258 Cedar St',
			is_verified=True,
			verification_status='verified'
		)
		
		self.client.login(username='voteruser', password='voterpass')
		url = reverse('voter_profile')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, 'voteruser')

	def test_voter_can_view_elections_list(self):
		"""Test voter can view list of active elections."""
		from .models import Voter
		voter = Voter.objects.create(
			user=self.voter_user,
			voter_id='V009',
			mobile='1111111111',
			address='369 Spruce St',
			is_verified=True,
			verification_status='verified'
		)
		
		self.client.login(username='voteruser', password='voterpass')
		url = reverse('voter_elections_list')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, 'Test Election')

	def test_voter_can_view_notifications(self):
		"""Test voter can view their notifications."""
		from .models import Voter, Notification
		voter = Voter.objects.create(
			user=self.voter_user,
			voter_id='V010',
			mobile='2222222222',
			address='741 Maple St',
			is_verified=True,
			verification_status='verified'
		)
		
		# Create a notification
		Notification.objects.create(
			voter=voter,
			title='Test Notification',
			message='This is a test',
			notification_type='system'
		)
		
		self.client.login(username='voteruser', password='voterpass')
		url = reverse('voter_notifications')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, 'Test Notification')

	def test_vote_creates_confirmation_notification(self):
		"""Test that casting a vote creates a confirmation notification."""
		from .models import Voter, Vote, Notification
		voter = Voter.objects.create(
			user=self.voter_user,
			voter_id='V011',
			mobile='3333333333',
			address='852 Oak Ave',
			is_verified=True,
			verification_status='verified'
		)
		
		self.client.login(username='voteruser', password='voterpass')
		url = reverse('voter_cast_vote', args=[self.election.id])
		data = {'candidate_id': self.candidate.id}
		self.client.post(url, data)
		
		# Check confirmation notification was created
		self.assertTrue(
			Notification.objects.filter(
				voter=voter,
				notification_type='vote_confirmation'
			).exists()
		)

	def test_voter_can_view_results(self):
		"""Test voter can view election results after election ends."""
		from .models import Voter, Vote
		from elections.models import Election
		from django.utils import timezone
		
		# Create a concluded election
		now = timezone.now()
		concluded = Election.objects.create(
			title='Concluded Election',
			election_type='single',
			start_date=now - timezone.timedelta(days=2),
			end_date=now - timezone.timedelta(days=1),
			is_active=False
		)
		concluded.candidates.add(self.candidate)
		
		voter = Voter.objects.create(
			user=self.voter_user,
			voter_id='V012',
			mobile='4444444444',
			address='963 Pine Ave',
			is_verified=True,
			verification_status='verified'
		)
		
		# Cast a vote
		Vote.objects.create(voter=voter, candidate=self.candidate, election=concluded)
		
		self.client.login(username='voteruser', password='voterpass')
		url = reverse('voter_view_results')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, 'Concluded Election')
