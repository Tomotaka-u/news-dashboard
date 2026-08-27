from pathlib import Path

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader


TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"


def get_template():
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    return env.get_template("index.html.j2")


def get_render_context(sns_data):
    return {
        "display_categories": [],
        "overall_total": 0,
        "all_sites": [],
        "ranking_data": [],
        "ranking_status": {
            "success_sources": 0,
            "total_sources": 0,
            "failed_sources": 0,
            "failed_names": [],
            "updated_at": "",
        },
        "source_status": [],
        "feed_status_by_name": {},
        "sns_data": sns_data,
        "bookmarks": [],
        "updated_at": "",
    }


def render_index(sns_data):
    return get_template().render(**get_render_context(sns_data))


def test_sns_tab_renders_grok_automations_cta_without_sns_post_data():
    marker = "DYNAMIC-SNS-CONTENT-MUST-NOT-BE-PUBLIC"
    html = render_index(
        [{
            "label": "日本で話題",
            "accent_color": "#ef4444",
            "icon_gradient": "linear-gradient(#fff, #000)",
            "badge": "JP",
            "posts": [{
                "author": "SNS-POST-AUTHOR",
                "content": marker,
                "url": "https://x.example/post",
            }],
        }]
    )

    soup = BeautifulSoup(html, "html.parser")
    sns_panel = soup.select_one('#tab-sns[role="tabpanel"]')
    assert sns_panel is not None

    cta = sns_panel.select_one("a.sns-cta-link")
    assert cta is not None
    assert cta["href"] == "https://grok.com/automations"
    assert cta["target"] == "_blank"
    assert "noopener" in cta.get("rel", [])
    assert "Grok Automations" in html
    assert "毎日の情報収集を自動化" in html
    assert marker not in html
    assert "SNS-POST-AUTHOR" not in html


def test_sns_card_markup_is_preserved_in_a_recovery_macro():
    module = get_template().make_module(get_render_context([]))
    legacy_html = str(module.legacy_sns_cards([{
        "label": "日本で話題",
        "accent_color": "#ef4444",
        "icon_gradient": "linear-gradient(#fff, #000)",
        "badge": "JP",
        "posts": [{
            "author": "Example Author",
            "content": "Example Content",
            "url": "https://x.example/post",
        }],
    }]))
    legacy_soup = BeautifulSoup(legacy_html, "html.parser")
    post_link = legacy_soup.select_one(".sns-grid .sns-post-list a")

    assert legacy_soup.select_one(".sns-grid") is not None
    assert "日本で話題" in legacy_soup.get_text()
    assert "JP" in legacy_soup.get_text()
    assert "Example Author" in legacy_soup.get_text()
    assert "Example Content" in legacy_soup.get_text()
    assert post_link["href"] == "https://x.example/post"
    assert post_link["target"] == "_blank"
    assert "noopener" in post_link.get("rel", [])
    assert "No SNS data available" in str(module.legacy_sns_cards([]))
