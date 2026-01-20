"""
Tests for the deepseek_ocr package
"""
import unittest
from unittest.mock import patch, MagicMock
from deepseek_ocr.parser import parse_bounding_box, parse_ocr_output
from deepseek_ocr.client import run_ollama_ocr


class TestParser(unittest.TestCase):
    def test_parse_bounding_box(self):
        """Test parsing bounding box strings"""
        bbox_str = "[[53, 123, 477, 435]]"
        result = parse_bounding_box(bbox_str)
        self.assertEqual(result, [53, 123, 477, 435])
    
    def test_parse_ocr_output(self):
        """Test parsing OCR output with references"""
        ocr_text = """
<|ref|>text<|/ref|><|det|>[[10, 20, 100, 50]]<|/det|>This is some text content.
<|ref|>image<|/ref|><|det|>[[150, 200, 300, 400]]<|/det|>
<|ref|>sub_title<|/ref|><|det|>[[10, 500, 200, 550]]<|/det|>Section Title
        """
        
        references, markdown = parse_ocr_output(ocr_text)
        
        # Check that we got 3 references
        self.assertEqual(len(references), 3)
        
        # Check first reference (text)
        self.assertEqual(references[0]['type'], 'text')
        self.assertEqual(references[0]['content'], 'This is some text content.')
        self.assertEqual(references[0]['bounding_box'], [10, 20, 100, 50])
        
        # Check second reference (image)
        self.assertEqual(references[1]['type'], 'image')
        
        # Check third reference (sub_title)
        self.assertEqual(references[2]['type'], 'sub_title')
        self.assertEqual(references[2]['content'], 'Section Title')
        
        # Check markdown was generated
        self.assertIn('This is some text content.', markdown)
        self.assertIn('Section Title', markdown)

    def test_parse_ocr_output_with_custom_image_url(self):
        """Test parsing OCR output with custom image URL generator"""
        ocr_text = """
<|ref|>image<|/ref|><|det|>[[150, 200, 300, 400]]<|/det|>
<|ref|>text<|/ref|><|det|>[[10, 20, 100, 50]]<|/det|>Some text.
<|ref|>image<|/ref|><|det|>[[400, 500, 600, 700]]<|/det|>
        """

        # Custom URL generator that uses sqids
        def custom_url_generator(image_index: int, ref_data: dict) -> str:
            fake_sqids = ['abc123', 'def456', 'ghi789']
            return fake_sqids[image_index]

        references, markdown = parse_ocr_output(ocr_text, custom_url_generator)

        # Check that we got 3 references
        self.assertEqual(len(references), 3)

        # Check markdown uses custom URLs
        self.assertIn('![Image](abc123)', markdown)
        self.assertIn('![Image](def456)', markdown)
        self.assertNotIn('output/image_', markdown)


class TestClient(unittest.TestCase):
    @patch('deepseek_ocr.client.ollama.Client')
    def test_run_ollama_ocr(self, mock_client_class):
        """Test running OCR with mocked Ollama client"""
        # Setup mock
        mock_client = MagicMock()
        mock_client.chat.return_value = {
            'message': {'content': 'Test OCR output'}
        }
        mock_client_class.return_value = mock_client
        
        # Call function
        result = run_ollama_ocr(
            image_path='/tmp/test.png',
            prompt='Test prompt',
            model='deepseek-ocr',
            host='http://localhost:11434'
        )
        
        # Check result
        self.assertEqual(result, 'Test OCR output')
        
        # Verify client was created with correct host
        mock_client_class.assert_called_once_with(host='http://localhost:11434')
        
        # Verify chat was called with correct parameters
        mock_client.chat.assert_called_once()
        call_args = mock_client.chat.call_args
        self.assertEqual(call_args[1]['model'], 'deepseek-ocr')


if __name__ == '__main__':
    unittest.main()
