from django.shortcuts import render
from django.http import HttpResponseRedirect
# Forms to use in pages
import forms
# Dictionaries to pass to template context
import dicts
# Models to access our db's tables
import models

## helper functions
def retrieveUser(userName):
    try:
        return models.User.objects.get(name=userName)
    except:
        return None

### Template Pages ###
def front_page(request):
    """ Front page; Enter credentials to be processed by the login view """

    return render(request, 'front_page.html',
                 {'login_data': dicts.login_data, 'login_form': forms.login(),
                  'reg_modal': dicts.reg_modal, 'reg_form': forms.userRegister()})

def clouds(request):
    """List projects and vms in user's clouds"""

    cloud_modals = [{'id': 'createProject', 'action': '/createProject', 'title': 'Create Project', 'form': forms.createProject()},
                    {'id': 'deleteProject', 'action': '/deleteProject', 'title': 'Delete Project', 'form': forms.deleteProject()},
                    {'id': 'createCluster', 'action': '/createCluster', 'title': 'Create Cluster', 'form': forms.createCluster()},
                    {'id': 'deleteCluster', 'action': '/deleteCluster', 'title': 'Delete Cluster', 'form': forms.deleteCluster()},
                    #{'id': 'createVM', 'title': 'Create VM', 'form': forms.createVM()},
                    {'id': 'deleteVM', 'title': 'Delete VM', 'form': forms.deleteVM()},]
    createVMform = forms.createVM()

    user = retrieveUser(request.session['username'])

    try:
        projects = models.UIProject.objects.filter(user=user)
    except:
        pass

    project_list = []
    for project in projects:
        vm_list = []
        for vm in models.VM.objects.filter(ui_project=project):
            vm_list.append(vm.name)
        project_list.append({'name':project.name, 'vm_list': vm_list})

    for project in dicts.test_project_list:
        project_list.append(project)


    return render(request, 'clouds.html', {'project_list': project_list, 'cloud_modals': cloud_modals, 'createVMform': createVMform })

### User Actions ###
def login(request):
    """ Login view; Checks post credentials, redirects
    to clouds or back to front page with error """
    if request.method == 'POST':
        form = forms.login(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = retrieveUser(username)
            if user is not None and user.verify_password(password=password):
                request.session['username'] = username
                return HttpResponseRedirect('/clouds')

    return HttpResponseRedirect('/')

def logout(request):
    """ Logout of session; remove session variables and return to login page """
    for state, sessionInfo in request.session.items():
        sessionInfo = None

    return HttpResponseRedirect('/')

def register(request):
    """ Register new user with keystone;
    called from login page Needs error checking """
    if request.method == "POST":
        form = forms.userRegister(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = retrieveUser(username)
            if user is None:
                newuser = models.User(name=username)
                newuser.set_password(password=password)
                newuser.save()
                request.session['username'] = username
                return HttpResponseRedirect('/clouds')

    return HttpResponseRedirect('/')

## Project form processing
def createProject(request):
    """
    Process form to create a project,
    if the project doesn't exist and user is registered,
    make new project in db
    """
    if request.method == "POST":
        form = forms.createProject(request.POST)
        if form.is_valid():
            print "form is valid"
            user = models.User.objects.get(name=request.session['username'])
            print user
            project_name = form.cleaned_data['name']
            print project_name

            try:
                project = models.UIProject(name=project_name, user=user)
                print project
            except:
                print "Error, project not made"
                project = None

            if project is not None:
                project.save()

    return HttpResponseRedirect('/clouds')

def deleteProject(request):
    """
    Process form to delete a project,
    if the project doesn't exist and user is registered,
    make new project in db
    """
    if request.method == "POST":
        form = forms.deleteProject(request.POST)
        if form.is_valid():
            user = retrieveUser(request.session['username'])
            project_name = form.cleaned_data['name']

            try:
                project = models.UIProject.objects.get(name=project_name, user=user)
            except:
                project = None

            if project is not None:
                project.delete()

    return HttpResponseRedirect('/clouds')

## cluster form processing
def createCluster(request):
    """
    Process form to create a cluster,
    if the cluster doesn't exist and user is registered,
    make new cluster in db
    """
    if request.method == "POST":
        form = forms.createCluster(request.POST)
        if form.is_valid():
            user = retrieveUser(request.session['username'])
            cluster_name = form.cleaned_data['name']
            cluster_user_name = form.cleaned_data['user_name']
            cluster_password = form.cleaned_data['password']
            endpoint = form.cleaned_data['endpoint']

            try:
                cluster = models.Cluster(name=cluster_name, user_name=cluster_user_name, password=cluster_password,
                                         endpoint=endpoint, user=user)
            except:
                cluster = None

            if cluster is not None:
                cluster.save()

    return HttpResponseRedirect('/clouds')

def deleteCluster(request):
    if request.method == "POST":
        form = forms.deleteCluster(request.POST)
        if form.is_valid():
            user = retrieveUser(request.session['username'])
            cluster_name = form.cleaned_data['name']
            action = form.cleaned_data['action']

            try:
                cluster = models.Cluster.objects.get(name=cluster_name, user=user)
            except:
                cluster = None

            if cluster is not None:
                cluster.delete()

    return HttpResponseRedirect('/clouds')

## vm form processing
def createVM(request):
    """Process form to create vm"""
    if request.method == "POST":
        form = forms.createVM(request.POST)
        if form.is_valid():
            user = retrieveUser(request.session['username'])
            vm_name = form.cleaned_data['name']
            os_project = form.cleaned_data['provider']
            nova = os_project.get_novaclient()
            try:
                nova_vm = nova.servers.find(name=vm_name)
                vm_model = models.VM.objects.get(uuid=nova_vm.to_dict()['id'])
            except models.VM.DoesNotExist:
                vm = None

            nova = os_project.get_novaclient()
            try:
                nova_vm = nova.servers.find(name=vm_name)
                vm_model = models.VM.objects.get(os_uuid=nova_vm.to_dict()['id'])
            except models.VM.DoesNotExist:
                vm_model = None

            if vm_model is None:
                nova_vm = os_project.create_vm(vm_name)
                vm_model = models.VM(os_uuid=nova_vm.to_dict()['id'],
                                     os_project=os_project,
                                     ui_project=user.uiproject_set[0],
                                     )
                vm_model.save()
    return HttpResponseRedirect('/clouds')

def deleteVM(request):
    """Process form to delete vm"""
#    if request.method == "POST":
#        form = forms.deleteVM(request.POST)
#        if form.is_valid():
#<<<<<<< HEAD
#            if form.cleaned_data['action'] != 'destroy':
#                raise NotImplemented
#            user = models.User.objects.get(name=request.session['username'])
#            vm_name = form.cleaned_data['name']
#            vm = models.VM.objects.get(name=vm_name, user=user)
#            nova = vm.os_project.get_novaclient()
#            #nova.servers.delete(
#            try:
#
#                if action == 'destroy' and 'pk' in vm:
#                    vm.delete()
#=======
#            user = retrieveUser(request.session['username'])
#            vm_name = form.cleaned_data['name']
#
#            try:
#                vm = models.VM.objects.get(name=vm_name, user=user)
#>>>>>>> stage3-fixups
#            except:
#                vm = None
#
#            if action == 'destroy' and vm is not None:
#                vm.delete()


def controlVM(request):
    """Control operations on vm"""
#    if request.method == "POST":
#        form = forms.controlVM(request.POST)
#        if form.is_valid():
#<<<<<<< HEAD
#            user = models.User.objects.get(name=request.session['username'])
#            vm = models.UIProject.objects.get(name=form.cleaned_data['name'],
#                                              user=user)
#            action = form.cleaned_data['action']
#
#            if vm is None:
#                # error here
#                return HttpResponseRedirect('/clouds')
#
#            nova = vm.os_project.get_novaclient()
#
#            if action is 'power_on':
#                nova.servers.start(vm.os_uuid)
#
#            if action is 'power_off':
#                nova.servers.stop(vm.os_uuid)
#=======
#            user_name = request.session['username']
#            vm_uuid = form.cleaned_data['name']
#            action = form.cleaned_data['action']
#
#            ## we need to ensure that our UUIDs cannot collide
#            try:
#                vm = models.VM.objects.get(uuid=vm_uuid)
#            except:
#                vm = None
#
#            if action is 'power_on' and vm is not None:
#                pass
#
#            if action is 'power_off' and vm is not None:
#                pass
#
#            if action is 'vnc' and vm is not None:
#                pass
#>>>>>>> stage3-fixups

    return HttpResponseRedirect('/clouds')
