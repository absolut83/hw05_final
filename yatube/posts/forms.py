from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        label = {'text': 'Введите текст', 'group': 'Выберите группу'}
        help_text = {'text': 'Напишите ваш текст тут',
                     'group': 'Из уже существующих'}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
