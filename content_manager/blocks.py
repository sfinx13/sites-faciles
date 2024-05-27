from django import forms
from django.conf import settings
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from dsfr.constants import COLOR_CHOICES, COLOR_CHOICES_ILLUSTRATION, COLOR_CHOICES_SYSTEM, IMAGE_RATIOS
from wagtail import blocks
from wagtail.blocks import StructValue
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtailmarkdown.blocks import MarkdownBlock

from content_manager.constants import HEADING_CHOICES, HORIZONTAL_CARD_IMAGE_RATIOS, LEVEL_CHOICES
from content_manager.widgets import DsfrIconPickerWidget


# Wagtail Block Documentation : https://docs.wagtail.org/en/stable/reference/streamfield/blocks.html


## Meta blocks
class BackgroundColorChoiceBlock(blocks.ChoiceBlock):
    choices = COLOR_CHOICES

    class Meta:
        icon = "view"


class LinkStructValue(blocks.StructValue):
    def url(self):
        external_url = self.get("external_url")
        page = self.get("page")
        return external_url or page.url


class LinkWithoutLabelBlock(blocks.StructBlock):
    page = blocks.PageChooserBlock(
        label=_("Page"),
        required=False,
        help_text=_("Link to a page of this site. Use either this or the external URL parameter."),
    )
    external_url = blocks.URLBlock(
        label=_("External URL"),
        required=False,
        help_text=_("Use either this or the Page parameter."),
    )

    class Meta:
        value_class = LinkStructValue
        icon = "link"


class LinkBlock(LinkWithoutLabelBlock):
    text = blocks.CharBlock(label=_("Link label"), required=False)

    class Meta:
        value_class = LinkStructValue
        icon = "link"


class LinksVerticalListBlock(blocks.StreamBlock):
    link = LinkBlock(label=_("Link"))

    class Meta:
        icon = "list-ul"
        template = "content_manager/blocks/links_vertical_list.html"


button_type_choices = (
    ("fr-btn", _("Primary")),
    ("fr-btn fr-btn--secondary", _("Secundary")),
    ("fr-btn fr-btn--tertiary", _("Tertiary")),
    ("fr-btn fr-btn--tertiary-no-outline", _("Tertiary without border")),
)


class ButtonBlock(LinkBlock):
    button_type = blocks.ChoiceBlock(label=_("Button type"), choices=button_type_choices, required=False)

    class Meta:
        value_class = LinkStructValue
        icon = "link"


class ButtonsHorizontalListBlock(blocks.StreamBlock):
    button = ButtonBlock(label=_("Button"))

    class Meta:
        icon = "list-ul"
        template = "content_manager/blocks/buttons_horizontal_list.html"


class ButtonsVerticalListBlock(blocks.StreamBlock):
    button = ButtonBlock(label=_("Button"))

    class Meta:
        icon = "list-ul"
        template = "content_manager/blocks/buttons_vertical_list.html"


class IconPickerBlock(blocks.FieldBlock):
    def __init__(self, required=True, help_text=None, validators=(), **kwargs):
        self.field_options = {
            "required": required,
            "help_text": help_text,
            "max_length": 70,
            "min_length": 0,
            "validators": [],
        }
        super().__init__(**kwargs)

    @cached_property
    def field(self):
        field_kwargs = {"widget": DsfrIconPickerWidget()}
        field_kwargs.update(self.field_options)
        return forms.CharField(**field_kwargs)

    class Meta:
        icon = "radio-full"


## Badges and Tags
badge_level_choices = (
    ("", [("new", _("New")), ("grey", _("Grey"))]),
    (_("System colors"), COLOR_CHOICES_SYSTEM),
    (_("Illustration colors"), COLOR_CHOICES_ILLUSTRATION),
)


class BadgeBlock(blocks.StructBlock):
    text = blocks.CharBlock(label=_("Badge label"), required=False)
    color = blocks.ChoiceBlock(label=_("Badge color"), choices=badge_level_choices, required=False)
    hide_icon = blocks.BooleanBlock(label=_("Hide badge icon"), required=False)

    class Meta:
        template = ("content_manager/blocks/badge.html",)


class BadgesListBlock(blocks.StreamBlock):
    badge = BadgeBlock(label=_("Badge"))

    class Meta:
        icon = "list-ul"
        template = "content_manager/blocks/badges_list.html"


class TagBlock(blocks.StructBlock):
    label = blocks.CharBlock(label=_("Title"))
    is_small = blocks.BooleanBlock(label=_("Small tag"), required=False)
    color = blocks.ChoiceBlock(
        label=_("Tag color"),
        choices=COLOR_CHOICES_ILLUSTRATION,
        required=False,
        help_text=_("Only for clickable tags"),
    )
    icon_class = IconPickerBlock(label=_("Icon"), required=False)
    link = LinkWithoutLabelBlock(required=False)

    class Meta:
        template = "content_manager/blocks/tag.html"


class TagListBlock(blocks.StreamBlock):
    tag = TagBlock(label=pgettext_lazy("DSFR Tag", "Tag"))

    class Meta:
        icon = "list-ul"
        template = "content_manager/blocks/tags_list.html"


## Cards


class CardstructValue(StructValue):
    def enlarge_link(self):
        """
        Determine if we need (and can) enlarge the link on the card.
        This requires:
        - That a link is present
        - That no other link is used on the card (such as a tag with a link, or a call-to-action)
        """
        url = self.get("url")
        document = self.get("document")
        top_detail_badges_tags = self.get("top_detail_badges_tags")
        call_to_action = self.get("call_to_action")

        if not (url or document):
            return False

        enlarge = True
        if len(call_to_action):
            enlarge = False
        elif len(top_detail_badges_tags) and top_detail_badges_tags.raw_data[0]["type"] == "tags":
            tags_list = top_detail_badges_tags.raw_data[0]["value"]
            for tag in tags_list:
                if tag["value"]["link"]["page"] is not None or tag["value"]["link"]["external_url"] != "":
                    enlarge = False

        return enlarge

    def image_classes(self):
        """
        Determine the image classes for a vertical card. Not used in horizontal card.
        """
        ratio_class = self.get("image_ratio")

        if ratio_class:
            image_classes = f"fr-responsive-img {ratio_class}"
        else:
            image_classes = "fr-responsive-img"

        return image_classes


class CardBlock(blocks.StructBlock):
    title = blocks.CharBlock(label=_("Title"))
    heading_tag = blocks.ChoiceBlock(
        label=_("Heading level"),
        choices=HEADING_CHOICES,
        default="h3",
        help_text=_("Adapt to the page layout. Defaults to heading 3."),
    )
    description = blocks.TextBlock(label=_("Content"), help_text=_("Can contain HTML."), required=False)
    image = ImageChooserBlock(label=_("Image"), required=False)
    image_ratio = blocks.ChoiceBlock(
        label=_("Image ratio"),
        choices=IMAGE_RATIOS,
        required=False,
        default="h3",
    )
    image_badge = BadgesListBlock(
        label=_("Image area badge"), required=False, help_text=_("Only used if the card has an image."), max_num=1
    )
    url = blocks.URLBlock(label=_("Link"), required=False, group="target")
    document = DocumentChooserBlock(
        label=_("or Document"),
        help_text=_("Select a document to make the card link to it (if the 'Link' field is not populated.)"),
        required=False,
        group="target",
    )
    top_detail_text = blocks.CharBlock(label=_("Top detail: text"), required=False)
    top_detail_icon = IconPickerBlock(label=_("Top detail: icon"), required=False)
    top_detail_badges_tags = blocks.StreamBlock(
        [
            ("badges", BadgesListBlock()),
            ("tags", TagListBlock()),
        ],
        label=_("Top detail: badges or tags"),
        max_num=1,
        required=False,
    )
    bottom_detail_text = blocks.CharBlock(
        label=_("Bottom detail: text"),
        help_text=_("Incompatible with the bottom call-to-action"),
        required=False,
    )
    bottom_detail_icon = IconPickerBlock(label=_("Bottom detail: icon"), required=False)
    call_to_action = blocks.StreamBlock(
        [
            ("links", LinksVerticalListBlock()),
            ("buttons", ButtonsHorizontalListBlock()),
        ],
        label=_("Bottom call-to-action: links or buttons"),
        help_text=_("Incompatible with the bottom detail text"),
        max_num=1,
        required=False,
    )
    grey_background = blocks.BooleanBlock(label=_("Card with grey background"), required=False)
    no_background = blocks.BooleanBlock(label=_("Card without background"), required=False)
    no_border = blocks.BooleanBlock(label=_("Card without border"), required=False)
    shadow = blocks.BooleanBlock(label=_("Card with a shadow"), required=False)

    class Meta:
        icon = "tablet-alt"
        template = "content_manager/blocks/card.html"
        value_class = CardstructValue


class HorizontalCardBlock(CardBlock):
    image_ratio = blocks.ChoiceBlock(
        label=_("Image ratio"),
        choices=HORIZONTAL_CARD_IMAGE_RATIOS,
        required=False,
        default="h3",
    )

    class Meta:
        icon = "tablet-alt"
        template = "content_manager/blocks/card_horizontal.html"
        value_class = CardstructValue


class VerticalCardBlock(CardBlock):
    class Meta:
        icon = "tablet-alt"
        template = "content_manager/blocks/card_vertical.html"
        value_class = CardstructValue


## Basic blocks
class AccordionBlock(blocks.StructBlock):
    title = blocks.CharBlock(label=_("Title"))
    content = blocks.RichTextBlock(label=_("Content"))


class AccordionsBlock(blocks.StreamBlock):
    title = blocks.CharBlock(label=_("Title"))
    accordion = AccordionBlock(label=_("Accordion"), min_num=1, max_num=15)


class AlertBlock(blocks.StructBlock):
    title = blocks.CharBlock(label=_("Message title"), required=False)
    description = blocks.TextBlock(label=_("Message text"), required=False)
    level = blocks.ChoiceBlock(label=_("Message type"), choices=LEVEL_CHOICES)
    heading_tag = blocks.ChoiceBlock(
        label=_("Heading level"),
        choices=HEADING_CHOICES,
        default="h3",
        help_text=_("Adapt to the page layout. Defaults to heading 3."),
    )


class CalloutBlock(blocks.StructBlock):
    title = blocks.CharBlock(label=_("Callout title"), required=False)
    text = blocks.TextBlock(label=_("Callout text"), required=False)
    heading_tag = blocks.ChoiceBlock(
        label=_("Heading level"),
        choices=HEADING_CHOICES,
        default="h3",
        help_text=_("Adapt to the page layout. Defaults to heading 3."),
    )


class IframeBlock(blocks.StructBlock):
    title = blocks.CharBlock(
        label=_("Title"),
        help_text=_("Accessibility: The title should describe, in a clear and concise manner, the embedded content."),
    )
    url = blocks.URLBlock(
        label=_("URL of the iframe"),
        help_text=_("Example for Tally: https://tally.so/embed/w2jMRa"),
    )
    height = blocks.IntegerBlock(label=_("Height (in pixels)"))

    class Meta:
        icon = "globe"
        template = "content_manager/blocks/iframe.html"


class ImageAndTextBlock(blocks.StructBlock):
    image = ImageChooserBlock(label=_("Image"))
    image_side = blocks.ChoiceBlock(
        label=_("Side where the image is displayed"),
        choices=[
            ("left", _("Left")),
            ("right", _("Right")),
        ],
        default="right",
    )
    image_ratio = blocks.ChoiceBlock(
        label=_("Image width"),
        choices=[
            ("3", "3/12"),
            ("5", "5/12"),
            ("6", "6/12"),
        ],
        default="3",
    )
    text = blocks.RichTextBlock(label=_("Rich text"))
    link = LinkBlock(
        label=_("Link"),
        required=False,
        help_text=_("The link is shown at the bottom of the text block, with an arrow"),
    )
    link_label = blocks.CharBlock(
        label=_("Link label (obsolete)"),
        required=False,
        help_text=_(
            "This field is obsolete and will be removed in the near future. Please replace with the Link field above."
        ),
        group="obsolete",
    )
    page = blocks.PageChooserBlock(
        label=_("Internal link (obsolete)"),
        required=False,
        help_text=_(
            "This field is obsolete and will be removed in the near future. Please replace with the Link field above."
        ),
        group="obsolete",
    )
    link_url = blocks.URLBlock(
        label=_("Link URL (obsolete)"),
        required=False,
        help_text=_(
            "This field is obsolete and will be removed in the near future. Please replace with the Link field above."
        ),
        group="obsolete",
    )

    class Meta:
        icon = "image"
        template = "content_manager/blocks/image_and_text.html"


class ImageBlock(blocks.StructBlock):
    title = blocks.CharBlock(label=_("Title"), required=False)
    heading_tag = blocks.ChoiceBlock(
        label=_("Heading level"),
        choices=HEADING_CHOICES,
        required=False,
        default="h3",
        help_text=_("Adapt to the page layout. Defaults to heading 3."),
    )
    image = ImageChooserBlock(label=_("Image"))
    alt = blocks.CharBlock(
        label=_("Alternative text (textual description of the image)"),
        required=False,
    )
    caption = blocks.CharBlock(label=_("Caption"), required=False)
    url = blocks.URLBlock(label=_("Link"), required=False)

    class Meta:
        icon = "image"
        template = "content_manager/blocks/image.html"


class QuoteBlock(blocks.StructBlock):
    image = ImageChooserBlock(label=_("Image"), required=False)
    quote = blocks.CharBlock(label=_("Quote"))
    author_name = blocks.CharBlock(label=_("Author name"))
    author_title = blocks.CharBlock(label=_("Author title"), required=False)
    color = blocks.ChoiceBlock(
        label=_("Color"),
        choices=COLOR_CHOICES_ILLUSTRATION,
        required=False,
    )

    class Meta:
        icon = "openquote"
        template = "content_manager/blocks/quote.html"


class SeparatorBlock(blocks.StructBlock):
    top_margin = blocks.IntegerBlock(label=_("Top margin"), min_value=0, max_value=15, default=3)
    bottom_margin = blocks.IntegerBlock(label=_("Bottom margin"), min_value=0, max_value=15, default=3)


class StepBlock(blocks.StructBlock):
    title = blocks.CharBlock(label=_("Title"))
    detail = blocks.TextBlock(label=_("Detail"))


class StepsListBlock(blocks.StreamBlock):
    step = StepBlock(label=_("Step"))


class StepperBlock(blocks.StructBlock):
    title = blocks.CharBlock(label=_("Title"))
    total = blocks.IntegerBlock(label=_("Number of steps"))
    current = blocks.IntegerBlock(label=_("Current step"))
    steps = StepsListBlock(label=_("Steps"))


class TextAndCTA(blocks.StructBlock):
    text = blocks.RichTextBlock(label=_("Rich text"), required=False)
    cta_label = blocks.CharBlock(
        label=_("Call to action label"),
        help_text=_("The link appears as a button under the text block"),
        required=False,
    )
    cta_url = blocks.CharBlock(label=_("Link"), required=False)

    class Meta:
        icon = "link"
        template = "content_manager/blocks/text_and_cta.html"


class VideoBlock(blocks.StructBlock):
    title = blocks.CharBlock(label=_("Title"), required=False)
    caption = blocks.CharBlock(label=_("Caption"))
    url = blocks.URLBlock(
        label=_("Video URL"),
        help_text="Use embed format (e.g. : https://www.youtube.com/embed/gLzXOViPX-0)",
    )

    class Meta:
        icon = "media"
        template = "content_manager/blocks/video.html"


## Page structure blocks
class CommonStreamBlock(blocks.StreamBlock):
    text = blocks.RichTextBlock(label=_("Rich text"))
    image = ImageBlock(label=_("Image"))
    video = VideoBlock(label=_("Video"))
    quote = QuoteBlock(label=_("Quote"))
    text_cta = TextAndCTA(label=_("Text and call to action"))
    iframe = IframeBlock(label=_("Iframe"))

    class Meta:
        icon = "dots-horizontal"


class MultiColumnsBlock(CommonStreamBlock):
    card = VerticalCardBlock(label=_("Vertical card"))

    class Meta:
        icon = "dots-horizontal"


class MultiColumnsWithTitleBlock(blocks.StructBlock):
    bg_image = ImageChooserBlock(label=_("Background image"), required=False)
    bg_color_class = BackgroundColorChoiceBlock(
        label=_("Background color"),
        required=False,
        help_text=_("Uses the French Design System colors"),
    )
    bg_color = blocks.RegexBlock(
        label=_("Background color, hexadecimal format (obsolete)"),
        regex=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
        help_text=_(
            "This field is obsolete and will be removed in the near future. Replace it with the background color."  # noqa
        ),
        error_messages={"invalid": _("Incorrect color format, must be #fff or #f5f5f5")},
        required=False,
    )
    title = blocks.CharBlock(label=_("Title"), required=False)
    heading_tag = blocks.ChoiceBlock(
        label=_("Heading level"),
        choices=HEADING_CHOICES,
        required=False,
        default="h2",
        help_text=_("Adapt to the page layout. Defaults to heading 2."),
    )
    columns = MultiColumnsBlock(label=_("Columns"))

    class Meta:
        icon = "dots-horizontal"
        template = "content_manager/blocks/multicolumns.html"


class FullWidthBlock(CommonStreamBlock):
    image_and_text = ImageAndTextBlock(label=_("Image and text"))
    card = HorizontalCardBlock(label=_("Horizontal card"))

    class Meta:
        icon = "minus"


class FullWidthBackgroundBlock(blocks.StructBlock):
    bg_image = ImageChooserBlock(label=_("Background image"), required=False)
    bg_color_class = BackgroundColorChoiceBlock(
        label=_("Background color"),
        required=False,
        help_text=_("Uses the French Design System colors"),
    )
    content = FullWidthBlock(label=_("Content"))

    class Meta:
        icon = "minus"
        template = "content_manager/blocks/full_width_background.html"


STREAMFIELD_COMMON_BLOCKS = [
    ("paragraph", blocks.RichTextBlock(label=_("Rich text"))),
    ("badges_list", BadgesListBlock(label=_("Badge list"))),
    ("image", ImageBlock()),
    ("imageandtext", ImageAndTextBlock(label=_("Image and text"))),
    ("alert", AlertBlock(label=_("Alert message"))),
    ("callout", CalloutBlock(label=_("Callout"))),
    ("quote", QuoteBlock(label=_("Quote"))),
    ("video", VideoBlock(label=_("Video"))),
    ("card", HorizontalCardBlock(label=_("Horizontal card"))),
    ("accordions", AccordionsBlock(label=_("Accordions"))),
    ("stepper", StepperBlock(label=_("Stepper"))),
    ("tags_list", TagListBlock(label=_("Tag list"))),
    ("markdown", MarkdownBlock(label=_("Markdown"))),
    ("separator", SeparatorBlock(label=_("Separator"))),
    ("multicolumns", MultiColumnsWithTitleBlock(label=_("Multiple columns"), group=_("Page structure"))),
    ("fullwidthbackground", FullWidthBackgroundBlock(label=_("Full width background"), group=_("Page structure"))),
]


# See warning on https://docs.wagtail.org/en/latest/reference/streamfield/blocks.html#wagtail.blocks.RawHTMLBlock
# There is currently no way to restrict a type of block depending on user permissions,
# pending issue https://github.com/wagtail/wagtail/issues/6323
if settings.SF_ALLOW_RAW_HTML_BLOCKS is True:
    STREAMFIELD_COMMON_BLOCKS += [
        (
            "html",
            blocks.RawHTMLBlock(
                readonly=True,
                help_text=_(
                    "Warning: Use HTML block with caution. Malicious code can compromise the security of the site."
                ),
            ),
        )
    ]
