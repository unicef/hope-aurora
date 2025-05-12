from typing import ReadOnly, TypedDict

from aurora.core.admin.form_editor import EventForm, FlexFormAttributesForm

type FormEditorTypes = type[FlexFormAttributesForm] | type[EventForm]

class FormEditorForms(TypedDict):
    frm: ReadOnly[FlexFormAttributesForm]
    events: EventForm
