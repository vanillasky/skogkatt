from skogkatt.commons.util.singleton import Singleton


class SingletonsSubCass(metaclass=Singleton):
    def __init__(self):
        self._name = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name


def test_instantiate():
    cls1 = SingletonsSubCass()
    cls1.name = "class1"
    id_of_cls1 = id(cls1)

    cls2 = SingletonsSubCass()
    cls2.name = "class2"
    id_of_cls2 = id(cls2)

    assert (id_of_cls1 == id_of_cls2)
    assert ("class2" == cls1.name)
    assert ("class2" == cls2.name)
