from app.services.ise import parse_ise_xml
from app.services.phones import to_ipa


SAMPLE_XML = """
<xml_result>
  <read_word lan="en">
    <rec_paper>
      <read_word total_score="64.5" accuracy_score="60" fluency_score="70" integrity_score="90">
        <sentence>
          <word content="cat" total_score="60">
            <syll serr_msg="1" content="k ae t">
              <phone content="k" dp_message="0" />
              <phone content="ae" dp_message="0" />
              <phone content="t" dp_message="0" />
            </syll>
          </word>
        </sentence>
      </read_word>
    </rec_paper>
  </read_word>
</xml_result>
"""

PHONE_XML = """
<xml_result>
  <read_word lan="en">
    <rec_paper>
      <read_word total_score="58" accuracy_score="50" fluency_score="70" integrity_score="90">
        <sentence>
          <word content="cat">
            <syll serr_msg="1" content="k ae t">
              <phone content="k" dp_message="0" score="90" />
              <phone content="ae" dp_message="128" score="40" />
              <phone content="t" dp_message="0" score="88" />
            </syll>
          </word>
        </sentence>
      </read_word>
    </rec_paper>
  </read_word>
</xml_result>
"""


def test_arpabet_to_ipa() -> None:
    assert to_ipa("ae") == "æ"
    assert to_ipa("IY") == "iː"
    assert to_ipa("θ") == "θ"


def test_parse_ise_xml_extracts_scores_and_error_phones() -> None:
    parsed = parse_ise_xml(SAMPLE_XML)
    assert parsed["overall_score"] == 64.5
    assert parsed["accuracy"] == 60.0
    assert parsed["error_symbols"] == ["ae"]
    assert "k" not in parsed["error_symbols"]
    assert "t" not in parsed["error_symbols"]
    assert parsed["syllable_errors"]
    assert parsed["phone_errors"][0]["kind"] == "syllable"


def test_parse_ise_xml_uses_phone_dp_message() -> None:
    parsed = parse_ise_xml(PHONE_XML)
    assert parsed["error_symbols"] == ["ae"]
    assert parsed["phone_errors"][0]["kind"] == "substitute"
    assert parsed["phone_errors"][0]["score"] == 40.0
