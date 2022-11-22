import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.views import generic
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect


from catalog.models import Book, Author, BookInstance, Genre
from catalog.forms import RenewBookForm, RenewBookModelForm, NewUserForm


def index(request):
    """View function for home page of site."""
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count() # The 'all()' is implied by default.

    # generate counts for genres and books that contain a particular word (case insensitive)
    num_genres = Genre.objects.all().count()
    # num_genres = 3
    num_book_the = Book.objects.filter(title__icontains='the').count()

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_genres': num_genres,
        'num_book_the': num_book_the,
        'num_visits': num_visits,
    }

    return render(request, 'catalog/index.html', context=context)

def register_request(request):
	if request.method == "POST":
		form = NewUserForm(request.POST)
		if form.is_valid():
			user = form.save()
			messages.success(request, "Registration successful." )
			return HttpResponseRedirect(reverse('index'))
		messages.error(request, "Unsuccessful registration. Invalid information.")
	form = NewUserForm()
	return render (request=request, template_name="catalog/register.html", context={"register_form":form})

class BookListView(generic.ListView):
    model = Book
    paginate_by = 4

class BookDetailView(generic.DetailView):
    model = Book

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 4

class AuthorDetailView(generic.DetailView):
    model = Author

class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


class LoanedBooksAllListView(PermissionRequiredMixin, generic.ListView):
    """Generic class-based view listing all books currently on loan. to view for a Librarian"""
    permission_required = 'catalog.can_mark_return'
    model = BookInstance
    template_name = 'catalog/bookinstance_list_all_borrowed.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


@login_required
@permission_required('catalog.can_mark_return', raise_exception=True)
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    #if this is a POST request then process the Form date
    if request.method == 'POST':
        #create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        #check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_ata as required (here we just write it to the model due_back field)
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            #redirect to a new URL:
            # messages.succes(request, 'renewal date succesfully updated.')
            succes_message = 'Due date for the book "' + str(book_instance.book.title) + '" from "' + str(book_instance.book.author.last_name) + '" was succesfully updated.'
            messages.add_message(request, messages.SUCCESS, succes_message)
            return HttpResponseRedirect(reverse('all-borrowed'))

    #if this is a GET (or any other methods) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})          

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)


@login_required
@permission_required('catalog.can_mark_return', raise_exception=True)
def renew_book_librarian_second_way(request, pk):
    """View function for renewing a specific BookInstance by librarian. Usage of ModelForm instead of Form"""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    #if this is a POST request then process the Form date
    if request.method == 'POST':
        #create a form instance and populate it with data from the request (binding):
        form = RenewBookModelForm(request.POST)

        #check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_ata as required (here we just write it to the model due_back field)
            book_instance.due_back = form.cleaned_data['due_back']
            book_instance.save()

            #redirect to a new URL:
            # messages.succes(request, 'renewal date succesfully updated.')
            succes_message = 'Due date for the book "' + str(book_instance.book.title) + '" from "' + str(book_instance.book.author.last_name) + '" was succesfully updated.'
            messages.add_message(request, messages.SUCCESS, succes_message)
            return HttpResponseRedirect(reverse('all-borrowed'))

    #if this is a GET (or any other methods) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookModelForm(initial={'due_back': proposed_renewal_date})          

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)


class AuthorCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'catalog.can_mark_return'
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_birth': '01/06/1991'}

class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'catalog.can_mark_return'
    model = Author
    fields = '__all__' # Not recommended (potential security issue if more fields added)

class AuthorDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'catalog.can_mark_return'
    model = Author
    success_url = reverse_lazy('authors')

class BookCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'catalog.can_mark_return'
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre']

class BookUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'catalog.can_mark_return'
    model = Book
    fields = '__all__' # Not recommended (potential security issue if more fields added)

class BookDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'catalog.can_mark_return'
    model = Book
    success_url = reverse_lazy('books')