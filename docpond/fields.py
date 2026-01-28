from django_sqids import SqidsField, shuffle_alphabet


class ModelSeedSqidsField(SqidsField):
    def __init__(self, min_length=4, seed=None, *args, **kwargs):
        self._seed = seed
        # pass a placeholder alphabet; we'll set it in contribute_to_class
        super().__init__(min_length=min_length, alphabet=None, *args, **kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        seed = self._seed or f"{cls._meta.app_label}_{cls.__name__}"
        self.alphabet = shuffle_alphabet(seed=seed)
        super().contribute_to_class(cls, name, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self._seed is not None:
            kwargs["seed"] = self._seed
        return name, path, args, kwargs