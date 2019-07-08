from annoying.functions import get_object_or_None
from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError


class Command(createsuperuser.Command):
    help = 'Crate a superuser, and allow password to be provided'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--password', dest='password', default=None,
            help='Specifies the password for the superuser.',
        )
        parser.add_argument(
            '--preserve', dest='preserve', default=False, action='store_true',
            help='Exit normally if the user already exists.',
        ),

        parser.add_argument(
            '--if-no-superuser', action='store_true', dest='if_no_superuser',
            help='Will only create the specified user if there is a super user does not currently exist')

    def handle(self, *args, **options):
        password = options.get('password')
        username = options.get('username')
        database = options.get('database')

        if options.get('if_no_superuser') and self.UserModel._default_manager.db_manager(database).filter(is_superuser=True).exists():
            self.stdout.write('Not creating super user since one already exists')
            return
        if password and not username:
            raise CommandError("--username is required if specifying --password")

        if username and options.get('preserve'):
            exists = self.UserModel._default_manager.db_manager(database).filter(username=username).exists()
            if exists:
                self.stdout.write("User exists, exiting normally due to --preserve")
                return

        super(Command, self).handle(*args, **options)

        if password:
            user = self.UserModel._default_manager.db_manager(database).get(username=username)
            user.set_password(password)
            user.save()
