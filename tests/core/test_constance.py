from unittest import mock
from unittest.mock import Mock

from bs4 import BeautifulSoup
from django import forms

from aurora.core.constance import WriteOnlyInput, WriteOnlyTextarea


class WriteOnlyTestForm(forms.Form):
    char = forms.CharField(widget=WriteOnlyInput())
    text = forms.CharField(widget=WriteOnlyTextarea())


def test_writeonlywidget(db):
    frm = WriteOnlyTestForm({"char": "123", "text": "456"})
    assert frm.is_valid()
    assert frm.cleaned_data == {"char": "123", "text": "456"}

    assert frm.fields["char"].widget.render("aaa", "123") == '<input type="text" name="aaa" value="***"\n>'
    assert (
        frm.fields["text"].widget.render("aaa", "123") == '<textarea name="aaa" cols="40" rows="10"\n>\n***</textarea>'
    )
    soup = BeautifulSoup(str(frm), "html.parser")
    textarea = soup.find(id="id_text")
    assert textarea.get_text() == "\n***"

    char = soup.find(id="id_char")
    assert char.get("value") == "***"

    with mock.patch("aurora.core.constance.config", Mock(char="123", text="456")):
        frm = WriteOnlyTestForm({"char": "***", "text": "***"})
        assert frm.is_valid()
        assert frm.cleaned_data == {"char": "123", "text": "456"}
        assert frm.fields["char"].widget.render("aaa", "123") == '<input type="text" name="aaa" value="***"\n>'
        assert (
            frm.fields["text"].widget.render("aaa", "123")
            == '<textarea name="aaa" cols="40" rows="10"\n>\n***</textarea>'
        )
        soup = BeautifulSoup(str(frm), "html.parser")
        textarea = soup.find(id="id_text")
        assert textarea.get_text() == "\n***"

        char = soup.find(id="id_char")
        assert char.get("value") == "***"
