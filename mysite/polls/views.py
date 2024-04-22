import base64
from multiprocessing import connection
import pickle
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
from .models import Question
from django.template import loader
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from .models import Choice, Question
from django.views import generic
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):  #Flaw 3 Injection flaw, to prevent SQL injection dont use Python string formatting to compose a query, safer alternative commented out below
        user_input = self.request.GET.get('user_filter', '')
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM polls_question WHERE title LIKE '%{}%'".format(user_input))
            return cursor.fetchall()

    """def get_queryset(self):
       
        return Question.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')[:5]"""


class DetailView(generic.DetailView):
    ...
    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'

#Flaw 4 Insecure deserialization, avoid deserializing data from untrusted sources. A safe serialization format as JSON could have been used

@csrf_exempt    #Flaw 5 CSRF, To fix this flaw i would have to remove the "@csrf_exempt"
def vote(request, question_id):
    if 'user_prefs' in request.COOKIES:
        try:
            user_prefs = pickle.loads(base64.b64decode(request.COOKIES['user_prefs']))
        except Exception as e:
            return HttpResponseBadRequest("Invalid user data")

    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        response = HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
        user_prefs = {'last_voted_question': question_id}
        response.set_cookie('user_prefs', base64.b64encode(pickle.dumps(user_prefs)).decode('utf-8'))
        return response
    """
    def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
    """