import markdown
from django.core.mail import send_mail
from django.core.mail.message import EmailMessage, EmailMultiAlternatives
from django.http.response import HttpResponseRedirect
from django.utils import timezone

from django.views.generic import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from interp.models import User, Task, Translation, ContentVersion, VersionParticle
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest, JsonResponse

from wkhtmltopdf.views import PDFTemplateView

from interp.utils import get_translate_edit_permission, can_save_translate, is_translate_in_editing


class Home(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        user = User.objects.get(username=request.user.username)
        # tasks = Task.objects.filter(is_published=True).values_list('id', 'title')
        tasks = []
        for task in Task.objects.filter(is_published=True):
            translation = Translation.objects.filter(user=user, task=task).first()
            is_editing = translation and is_translate_in_editing(translation)
            freeze = translation and translation.freeze
            tasks.append((task.id, task.title, is_editing, freeze))

        return render(request, 'questions.html', context={'tasks': tasks, 'language': user.credentials()})


class Questions(LoginRequiredMixin,View):
    def get(self,request,id):
        user = User.objects.get(username=request.user)
        task = Task.objects.get(id=id)
        if task.is_published == False:
            return HttpResponseBadRequest("There is no published task")
        task_text = task.get_published_text()
        try:
            trans = Translation.objects.get(user=user, task=task)
        except:
            trans = Translation.objects.create(user=user, task=task, language=user.language)
            trans.add_version(task_text)
        if trans.freeze:
            return HttpResponseForbidden("This task is freezed")
        return render(request, 'editor.html',
                          context={'trans': trans.get_latest_text(), 'task': task_text, 'rtl': user.language.rtl,
                                   'quesId': id, 'language': str(user.language.name + '-' + user.country.name)})


class AccessTranslationEdit(LoginRequiredMixin, View):
    def post(selfs, request, id):
        edit_token = request.POST.get('edit_token', '')
        task = Task.objects.get(id=id)
        user = User.objects.get(username=request.user)
        if not task.is_published:
            return HttpResponseBadRequest("There is no published task")
        translation = Translation.objects.get(user=user, task=task)
        if user != translation.user:
            return HttpResponseForbidden()
        can_edit, new_edit_token = get_translate_edit_permission(translation, edit_token)
        return JsonResponse({'can_edit': can_edit, 'edit_token': new_edit_token})


class TranslatePreview(LoginRequiredMixin,View):
    def get(self,request,id):
        user = User.objects.get(username=request.user)
        task = Task.objects.get(id=id)
        if task.is_published == False:
            return HttpResponseBadRequest("There is no published task")
        task_text = task.get_published_text()
        try:
            trans = Translation.objects.get(user=user, task=task)
        except:
            trans = Translation.objects.create(user=user, task=task, language=user.language)
            trans.add_version(task_text)

        return render(request, 'preview.html',
                          context={'trans': trans.get_latest_text(), 'task': task_text, 'rtl': user.language.rtl,
                                   'quesId': id,
                                   'language': str(user.language.name + '-' + user.country.name)})


class SaveQuestion(LoginRequiredMixin,View):
    def post(self,request):
        id = request.POST['id']
        content = request.POST['content']
        edit_token = request.POST.get('edit_token', '')
        task = Task.objects.get(id=id)
        user = User.objects.get(username=request.user)
        translation = Translation.objects.get(user=user,task=task)
        if user != translation.user or not can_save_translate(translation, edit_token) or translation.freeze:
            return JsonResponse({'can_edit': False, 'edit_token': '', 'error': 'forbidden'})
        translation.add_version(content)
        VersionParticle.objects.filter(translation=translation).delete()
        can_edit, new_edit_token = get_translate_edit_permission(translation, edit_token)
        return JsonResponse({'can_edit': can_edit, 'edit_token': new_edit_token})


class Versions(LoginRequiredMixin,View):
    def get(self,request,id):
        user = User.objects.get(username=request.user)
        task = Task.objects.get(id=id)
        try:
            trans = Translation.objects.get(user=user,task=task)
        except:
            trans = Translation.objects.create(user=user, task=task, language=user.language, )

        v = []
        vp = []
        versions = trans.versions.all()
        version_particles = VersionParticle.objects.filter(translation=trans).order_by('date_time')
        for item in version_particles:
            vp.append((item.id,item.date_time))
        for item in versions:
            v.append((item.id,item.create_time))

        return render(request,'versions.html', context={'versions' : v , 'versionParticles':vp ,'translation' : trans.get_latest_text(), 'quesId':trans.id})


class GetVersion(LoginRequiredMixin,View):
    def get(self,request):
        id = request.GET['id']
        version = ContentVersion.objects.get(id=id)
        user = User.objects.get(username=request.user.username)
        if version.content_type.model != 'translation' or version.content_object.user != user:
            return HttpResponseBadRequest()
        return HttpResponse(version.text)


class GetVersionParticle(LoginRequiredMixin,View):
    def get(self,request):
        id = request.GET['id']
        version_particle = VersionParticle.objects.get(id=id)
        user = User.objects.get(username=request.user.username)
        if version_particle.translation.user != user:
            return HttpResponseForbidden()
        return HttpResponse(version_particle.text)


class SaveVersionParticle(LoginRequiredMixin,View):
    def post(self,request):
        id = request.POST['id']
        content = request.POST['content']
        task = Task.objects.get(id=id)
        user = User.objects.get(username=request.user.username)
        edit_token = request.POST.get('edit_token', '')
        translation = Translation.objects.get(user=user, task=task)
        if user != translation.user or not can_save_translate(translation, edit_token) or translation.freeze:
            return JsonResponse({'can_edit': False, 'edit_token': '', 'error': 'forbidden'})
        if translation.get_latest_text().strip() == content.strip():
            return JsonResponse({'can_edit': False, 'edit_token': '', 'error': 'Not Modified'})
        last_version_particle = translation.versionparticle_set.order_by('-date_time').first()
        if last_version_particle:
            last_version_particle.text = content
            last_version_particle.save()
        else:
            last_version_particle = VersionParticle.objects.create(translation=translation, text=content, date_time=timezone.now())
        can_edit, new_edit_token = get_translate_edit_permission(translation, edit_token)
        return JsonResponse({'can_edit': can_edit, 'edit_token': new_edit_token})

class GetTranslatePreview(LoginRequiredMixin,View):
    def get(self,request):
        task_id = self.request.GET['id']
        task = Task.objects.get(id=task_id)
        user = User.objects.get(username=request.user.username)
        translation = Translation.objects.get(user=user, task=task)
        # TODO check if it's available
        direction = 'rtl' if translation.language.rtl else 'ltr'
        return render(request, 'pdf_template.html', context={'content': translation.get_latest_text(),\
                    'direction': direction, 'title': "%s-%s" % (task.title, translation.language)})


class GetTranslatePDF(LoginRequiredMixin, PDFTemplateView):
    filename = 'my_pdf.pdf'
    template_name = 'pdf_template.html'
    cmd_options = {
        'page-size': 'Letter',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        # 'zoom': 1,
        'footer-center': '[page]/[topage]',
        # 'header-right': '<h3>Hello</h3>',
        # 'header-html': 'http://localhost:8000/static/pdf_header.html',
        # 'header-html': 'google.com',
        # 'header-line': True,
        # 'header-spacing': 3,
        # 'footer-line': True,
        # 'footer-spacing': 3,
        'javascript-delay': 500,
    }

    def get_context_data(self, **kwargs):
        context = super(GetTranslatePDF, self).get_context_data(**kwargs)
        task_id = self.request.GET['id']

        user = User.objects.get(username=self.request.user.username)
        task = Task.objects.filter(id=task_id).first()
        if task is None:
            # TODO
            return None

        trans = Translation.objects.filter(user=user, task=task).first()
        if trans is None:
            # TODO
            return None

        self.filename = "%s-%s" % (task.title, trans.language)
        content = trans.get_latest_text()
        context['direction'] = 'rtl' if trans.language.rtl else 'ltr'
        context['content'] = content
        context['title'] = self.filename
        from django.contrib.staticfiles.templatetags.staticfiles import static
        # print(static('pdf_header.html'))
        # print(self.request.build_absolute_uri(static('pdf_header.html')))
        # self.cmd_options['header-html'] = self.request.build_absolute_uri(static('pdf_header.html'))
        self.cmd_options['header-html'] = 'google.com'
        # from django.template import Context, Template
        # from django.utils.safestring import mark_safe
        # t = Template('This is your <span>{{ message }}</span>.')
        #
        # c = Context({'message': 'Your message'})
        # html = t.render(c)
        # print()
        # self.cmd_options['header-right'] = mark_safe(html)
        return context


class MailTranslatePDF(GetTranslatePDF):
    def get(self, request, *args, **kwargs):
        response = super(MailTranslatePDF, self).get(request, *args, **kwargs)
        response.render()

        subject, from_email, to = 'hello', 'navidsalehn@gmail.com', 'navidsalehn@gmail.com'
        text_content = 'Test'
        html_content = '<p>This is an <strong>TEST</strong> message.</p>'
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.attach('file.pdf', response.content, 'application/pdf')
        msg.send()

        return HttpResponseRedirect(request.META['HTTP_REFERER'])
