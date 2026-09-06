from huey.contrib.sql_huey import SqlStorage


class SqlStorageWithTablePrefix(SqlStorage):
    def create_models(self):
        models = super().create_models()
        for model in models:
            model._meta.set_table_name("huey_" + model.__name__.lower())
            if model.__name__ == "Task":
                for index in model._meta.indexes:
                    index._model = model
        return models
