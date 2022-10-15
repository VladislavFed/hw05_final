from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Group, Post, User


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
        )
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def post_create_form(self):
        """Валидная форма создает запись в БД."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текстовый текст',
            'group': self.group.slug,
            'image': uploaded,
        }
        post_latest = Post.objects.latest('id')
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                "posts:profile",
                kwargs={"username": self.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
                        text=form_data['text'],
                        group=self.group.id,
                        author=self.user
                        ).exists())
        self.assertEqual(post_latest.text, form_data['text'])
        self.assertEqual(post_latest.group.id, form_data['group'])
        self.assertEqual(post_latest.group.id, form_data['image'])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def post_edit_form(self):
        """Валидная форма редактирует запись в БД."""
        posts_count = Post.objects.count()
        form_data = {'text': 'Тестовый текст'}
        edit_post = Post.objects.get(id=self.post.id)
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(edit_post.text, form_data['text'])
        self.assertEqual(edit_post.author, self.post.author)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def comment_add_authorized_client(self):
        """Комментарий может может добавлять только авторизованный клиент."""
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.author,
        )
        comment = Comment.objects.latest('id')
        form_data = {
            'text': 'Текстовый текст',
            'author': self.author,
        }
        comments_count = Comment.objects.count
        response = self.authorized_client.get(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}),
            data=form_data,
            follow=True)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, form_data['author'])
        self.assertRedirects(
            response, reverse('posts:post_detail', args={post.id}))

    def comment_not_add_guest_client(self):
        """Не авторизованный клиент не может добавить комментарий."""
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.author,
        )
        comment = Comment.objects.latest('id')
        form_data = {'text': 'Текстовый текст', }
        comments_count = Comment.objects.count
        response = self.guest_client.get(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}),
            data=form_data,
            follow=True)
        redirect = reverse('login') + '?next=' + reverse(
            'posts:add_comment', kwargs={'post_id': post.id})
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertEqual(comment.text, form_data['text'])
        self.assertRedirects(response, redirect)
