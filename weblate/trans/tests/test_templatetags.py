#
# Copyright © 2012 - 2021 Michal Čihař <michal@cihar.com>
#
# This file is part of Weblate <https://weblate.org/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
"""Testing of template tags."""

import datetime
import unittest

from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from weblate.accounts.models import Profile
from weblate.lang.models import Language
from weblate.trans.models import Component, Project, Translation, Unit
from weblate.trans.templatetags.translations import (
    format_translation,
    get_location_links,
    naturaltime,
)
from weblate.trans.tests.test_views import FixtureTestCase

TEST_DATA = (
    (0, "now"),
    (1, "a second from now"),
    (-1, "a second ago"),
    (2, "2 seconds from now"),
    (-2, "2 seconds ago"),
    (60, "a minute from now"),
    (-60, "a minute ago"),
    (120, "2 minutes from now"),
    (-120, "2 minutes ago"),
    (3600, "an hour from now"),
    (-3600, "an hour ago"),
    (3600 * 2, "2 hours from now"),
    (-3600 * 2, "2 hours ago"),
    (3600 * 24, "tomorrow"),
    (-3600 * 24, "yesterday"),
    (3600 * 24 * 2, "2 days from now"),
    (-3600 * 24 * 2, "2 days ago"),
    (3600 * 24 * 7, "a week from now"),
    (-3600 * 24 * 7, "a week ago"),
    (3600 * 24 * 14, "2 weeks from now"),
    (-3600 * 24 * 14, "2 weeks ago"),
    (3600 * 24 * 30, "a month from now"),
    (-3600 * 24 * 30, "a month ago"),
    (3600 * 24 * 60, "2 months from now"),
    (-3600 * 24 * 60, "2 months ago"),
    (3600 * 24 * 365, "a year from now"),
    (-3600 * 24 * 365, "a year ago"),
    (3600 * 24 * 365 * 2, "2 years from now"),
    (-3600 * 24 * 365 * 2, "2 years ago"),
)


class NaturalTimeTest(SimpleTestCase):
    """Testing of natural time conversion."""

    def test_natural(self):
        now = timezone.now()
        for diff, expected in TEST_DATA:
            testdate = now + datetime.timedelta(seconds=diff)
            result = naturaltime(testdate, now)
            expected = '<span title="{}">{}</span>'.format(
                testdate.replace(microsecond=0).isoformat(), expected
            )
            self.assertEqual(
                expected,
                result,
                f'naturaltime({testdate}) "{result}" != "{expected}"',
            )


class LocationLinksTest(TestCase):
    def setUp(self):
        self.unit = Unit(
            translation=Translation(
                component=Component(
                    project=Project(slug="p", name="p"),
                    source_language=Language(),
                    slug="c",
                    name="c",
                ),
                language=Language(),
            )
        )
        self.unit.source_unit = self.unit
        self.profile = Profile()

    def test_empty(self):
        self.assertEqual(get_location_links(self.profile, self.unit), "")

    def test_numeric(self):
        self.unit.location = "123"
        self.assertEqual(get_location_links(self.profile, self.unit), "string ID 123")

    def test_filename(self):
        self.unit.location = "f&oo.bar:123"
        self.assertEqual(
            get_location_links(self.profile, self.unit), "f&amp;oo.bar:123"
        )

    def test_filenames(self):
        self.unit.location = "foo.bar:123,bar.foo:321"
        self.assertEqual(
            get_location_links(self.profile, self.unit), "foo.bar:123\nbar.foo:321"
        )

    def test_repowebs(self):
        self.unit.translation.component.repoweb = (
            "http://example.net/{{filename}}#L{{line}}"
        )
        self.unit.location = "foo.bar:123,bar.foo:321"
        self.assertHTMLEqual(
            get_location_links(self.profile, self.unit),
            """
            <a class="wrap-text"
                href="http://example.net/foo.bar#L123" target="_blank"
                dir="ltr" rel="noopener noreferrer">
            foo.bar:123
            </a>
            <a class="wrap-text"
                href="http://example.net/bar.foo#L321" target="_blank"
                dir="ltr" rel="noopener noreferrer">
            bar.foo:321
            </a>
            """,
        )

    def test_repoweb(self):
        self.unit.translation.component.repoweb = (
            "http://example.net/{{filename}}#L{{line}}"
        )
        self.unit.location = "foo.bar:123"
        self.assertHTMLEqual(
            get_location_links(self.profile, self.unit),
            """
            <a class="wrap-text"
                href="http://example.net/foo.bar#L123" target="_blank"
                dir="ltr" rel="noopener noreferrer">
            foo.bar:123
            </a>
            """,
        )

    def test_user_url(self):
        self.unit.translation.component.repoweb = (
            "http://example.net/{{filename}}#L{{line}}"
        )
        self.profile.editor_link = "editor://open/?file={{filename}}&line={{line}}"
        self.unit.location = "foo.bar:123"
        self.assertHTMLEqual(
            get_location_links(self.profile, self.unit),
            """
            <a class="wrap-text"
                href="editor://open/?file=foo.bar&amp;line=123" target="_blank"
                dir="ltr" rel="noopener noreferrer">
            foo.bar:123
            </a>
            """,
        )


class TranslationFormatTestCase(FixtureTestCase):
    def setUp(self):
        super().setUp()
        self.translation = self.get_translation()

    def test_basic(self):
        self.assertEqual(
            format_translation("Hello world", self.component.source_language,)["items"][
                0
            ]["content"],
            "Hello world",
        )

    def test_diff(self):
        self.assertEqual(
            format_translation(
                "Hello world",
                self.component.source_language,
                diff="Hello, world!",
            )["items"][0]["content"],
            "Hello<del>,</del> world<del>!</del>",
        )

    def test_glossary(self):
        self.assertHTMLEqual(
            format_translation(
                "Hello world",
                self.component.source_language,
                glossary=[
                    Unit(source="hello", target="ahoj", translation=self.translation)
                ],
            )["items"][0]["content"],
            """
            <span class="glossary-term"
                title="Glossary translation: ahoj">Hello</span>
            world
            """,
        )

    @unittest.expectedFailure
    def test_glossary_multi(self):
        self.assertHTMLEqual(
            format_translation(
                "Hello glossary",
                self.component.source_language,
                glossary=[
                    Unit(source="hello", target="ahoj", translation=self.translation),
                    Unit(
                        source="glossary", target="glosář", translation=self.translation
                    ),
                ],
            )["items"][0]["content"],
            """
            <span class="glossary-term"
                title="Glossary translation: ahoj">Hello</span>
            <span class="glossary-term"
                title="Glossary translation: glosář">glossary</span>
            """,
        )
