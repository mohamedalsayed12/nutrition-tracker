from logging.config import fileConfig

from alembic import context
from flask import current_app


config = context.config
fileConfig(config.config_file_name)
database = current_app.extensions["migrate"].db
metadata = database.metadata


def run_migrations():
    if context.is_offline_mode():
        context.configure(url=database.engine.url.render_as_string(hide_password=False),
                          target_metadata=metadata, literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
    else:
        with database.engine.connect() as connection:
            context.configure(connection=connection, target_metadata=metadata,
                              **current_app.extensions["migrate"].configure_args)
            with context.begin_transaction():
                context.run_migrations()


run_migrations()
