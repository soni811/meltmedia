import hippo.util as c
import time

from src.the_ark import input_generator
from src.the_ark.field_handlers import STRING_FIELD, EMAIL_FIELD, PHONE_FIELD, ZIP_CODE_FIELD, DATE_FIELD
from src.the_ark.screen_capture import FIREFOX_HEAD_HEIGHT


class Action:
    def __init__(self, screenshot_thread, selenium_helper, custom_inputs, padding):
        self.t = screenshot_thread
        self.sh = selenium_helper
        self.custom_inputs = custom_inputs
        self.padding = padding
        self.iteration = 0

    def capture(self, action, element):
        suffix = action.get(c.SUFFIX_KEY, "")
        padding = action.get(c.SCROLL_PADDING_KEY, "")
        full_name = action.get(c.FULL_NAME_KEY)
        current_url = action.get(c.CURRENT_URL_KEY, False)
        viewport_only = action.get(c.VIEWPORT_ONLY_KEY, False)
        add_to_misc = action.get(c.ADD_TO_MISC_KEY, False)

        if self.iteration != 0:
            suffix = f"{suffix}_{self.iteration:.03f}" if suffix else "{self.iteration:.03f}"

        # - Separate into launch capture calls based on available data
        if full_name:
            self.t.launch_capture(viewport_only=viewport_only, full_name=full_name, suffix=suffix, padding=padding, add_to_misc=add_to_misc)

        elif current_url:
            self.t.launch_capture(viewport_only=viewport_only, current_url=current_url, suffix=suffix, padding=padding, add_to_misc=add_to_misc)

        elif suffix:
            self.t.launch_capture(viewport_only=viewport_only, suffix=suffix, padding=padding, add_to_misc=add_to_misc)

        else:
            self.t.launch_capture(viewport_only=viewport_only, padding=padding, add_to_misc=add_to_misc)

    def capture_scrolling_element(self, action, element):
        suffix = action.get(c.SUFFIX_KEY, "")
        full_name = action.get(c.FULL_NAME_KEY, "")
        current_url = action.get(c.CURRENT_URL_KEY, False)
        viewport_only = action.get(c.VIEWPORT_ONLY_KEY, False)
        padding = action.get(c.SCROLL_PADDING_KEY, self.padding)
        css_selector = action.get(c.CSS_SELECTOR_KEY)
        add_to_misc = action.get(c.ADD_TO_MISC_KEY, False)

        if self.iteration:
            suffix = "{suffix}_{self.iteration:.03f}"
        self.t.launch_capture_scrolling_element(css_selector, full_name, suffix, current_url, padding, viewport_only,
                                                add_to_misc)

    def capture_element(self, action, element):
        suffix = action.get(c.SUFFIX_KEY, "")
        full_name = action.get(c.FULL_NAME_KEY, "")
        current_url = action.get(c.CURRENT_URL_KEY, False)
        padding = action.get(c.PADDING_KEY, 0)
        css_selector = action.get(c.CSS_SELECTOR_KEY)
        add_to_misc = action.get(c.ADD_TO_MISC_KEY, False)

        # - Capture the current size of the brwoser window
        window_width, window_height = self.sh.get_window_size()

        if css_selector and not action.get(c.ELEMENT_KEY):
            element = None

        # - Actions to set up the page
        # TODO: Make the browser skin buffer dynamic. 80 pixels is for Firefox
        # Resize Browser to fit element, with 80 pixel buffer for browser skin
        element_height = self.sh.get_element_size(css_selector, element)
        self.sh.resize_browser(height=element_height + 80 + (padding * 2))
        # Scroll to the element location minus the given padding
        self.sh.scroll_to_element(css_selector, element, offset=padding * -1)

        # - Take a viewport_only screenshot
        if self.iteration:
            suffix = f"{suffix}_{self.iteration:.03f}"

        self.t.launch_capture(full_name=full_name, suffix=suffix, current_url=current_url, viewport_only=True,
                              add_to_misc=add_to_misc)

        # - Put the window back to its rightful size
        self.resize_browser({c.WIDTH_KEY: window_width, c.HEIGHT_KEY: window_height}, None)

    def load_url(self, action, element):
        path = action[c.PATH_KEY]
        test_url = c.concatenate_test_url(self.t.base_url, path, self.t.content_path)

        # - Always bypass the 404 check on author environments because the request library that does
        # the check is not authorized to check, returning a 401
        bypass = True if self.t.author else action.get(c.BYPASS_404_KEY, False)

        self.sh.load_url(test_url, bypass)
        c.close_iperceptions(self.sh)
        c.close_gene_cookie_modal(self.sh)

    def click(self, action, element):
        if element and action.get(c.ELEMENT_KEY):
            self.sh.click_an_element(web_element=element)
        else:
            self.sh.click_an_element(action[c.CSS_SELECTOR_KEY])

    def click_element_with_offset(self, action, element):
        if element and action.get(c.ELEMENT_KEY):
            self.sh.click_element_with_offset(web_element=element, x_position=action.get(c.X_POSITION_KEY, 0),
                                              y_position=action.get(c.Y_POSITION_KEY, 0))
        else:
            self.sh.click_element_with_offset(action[c.CSS_SELECTOR_KEY], x_position=action.get(c.X_POSITION_KEY, 0),
                                              y_position=action.get(c.Y_POSITION_KEY, 0))

    def hover(self, action, element):
        if element and action.get(c.ELEMENT_KEY):
            self.sh.hover_on_element(web_element=element)
        else:
            self.sh.hover_on_element(action[c.CSS_SELECTOR_KEY])

    def enter_text(self, action, element):
        text = "Not-Configured"

        if action.get(c.INPUT_TYPE_KEY):
            input_type = action.get(c.INPUT_TYPE_KEY)
            if input_type == STRING_FIELD:
                text = input_generator.generate_string()
            elif input_type == EMAIL_FIELD:
                text = input_generator.generate_email()
            elif input_type == ZIP_CODE_FIELD:
                text = input_generator.generate_zip_code()
            elif input_type == PHONE_FIELD:
                text = input_generator.generate_phone()
            elif input_type == DATE_FIELD:
                text = input_generator.generate_date()
        elif action.get(c.CUSTOM_INPUT_KEY):
            custom_key = action.get(c.CUSTOM_INPUT_KEY)
            text = self.custom_inputs.get(custom_key, text)
        else:
            text = action[c.INPUT_KEY]
            if text == "brand":
                text = self.t.project

        if element and action.get(c.ELEMENT_KEY):
            self.sh.fill_an_element(text, web_element=element)
        else:
            self.sh.fill_an_element(text, action[c.CSS_SELECTOR_KEY])

    def scroll_window_to_position(self, action, element):
        self.sh.scroll_window_to_position(action.get(c.Y_POSITION_KEY, 0),
                                          action.get(c.X_POSITION_KEY, 0),
                                          action.get(c.POSITION_TOP_KEY, 0),
                                          action.get(c.POSITION_BOTTOM_KEY, 0))

    def scroll_window_to_element(self, action, element):
        if element and action.get(c.ELEMENT_KEY):
            self.sh.scroll_to_element(web_element=element,
                                      position_bottom=action.get(c.POSITION_BOTTOM_KEY),
                                      position_middle=action.get(c.POSITION_MIDDLE_KEY))
        else:
            self.sh.scroll_to_element(action[c.CSS_SELECTOR_KEY],
                                      position_bottom=action.get(c.POSITION_BOTTOM_KEY),
                                      position_middle=action.get(c.POSITION_MIDDLE_KEY))

    def scroll_an_element(self, action, element):
        y_pos = action.get(c.Y_POSITION_KEY)
        x_pos = action.get(c.X_POSITION_KEY)
        padding = action.get(c.SCROLL_PADDING_KEY)
        top = action.get(c.POSITION_TOP_KEY)
        bottom = action.get(c.POSITION_BOTTOM_KEY)

        if element and action.get(c.ELEMENT_KEY):
            self.sh.scroll_an_element(web_element=element, y_position=y_pos, x_position=x_pos,
                                      scroll_padding=padding, scroll_top=top, scroll_bottom=bottom)
        else:
            self.sh.scroll_an_element(css_selector=action[c.CSS_SELECTOR_KEY], y_position=y_pos,
                                      x_position=x_pos, scroll_padding=padding, scroll_top=top,
                                      scroll_bottom=bottom)

    def refresh(self, action, element):
        self.sh.refresh_driver()

    def sleep(self, action, element):
        time.sleep(action[c.DURATION_KEY])

    def wait_for_element(self, action, element):
        self.sh.wait_for_element(
            css_selector=action[c.CSS_SELECTOR_KEY], wait_time=action.get(c.DURATION_KEY, 15),
            visible=action.get(c.VISIBLE_KEY, False))

    def send_special_key(self, action, element):
        self.sh.send_special_key(action[c.SPECIAL_KEY_KEY])

    def reference(self, action, element):
        reference_key = action[c.REFERENCE_KEY]
        if isinstance(reference_key, list):
            for reference in reference_key:
                self.t.dispatch_actions(self.t.reference_actions[reference])
        else:
            self.t.dispatch_actions(self.t.reference_actions[reference_key])

    def show_element(self, action, element):
        if element and action.get(c.ELEMENT_KEY):
            self.sh.show_element(web_element=element)
        else:
            self.sh.show_element(action[c.CSS_SELECTOR_KEY])

    def hide_element(self, action, element):
        if element and action.get(c.ELEMENT_KEY):
            self.sh.hide_element(web_element=element)
        else:
            self.sh.hide_element(action[c.CSS_SELECTOR_KEY])

    def execute_script(self, action, element):
        if element and action.get(c.ELEMENT_KEY):
            self.sh.execute_script(action[c.SCRIPT_KEY], element)
        else:
            self.sh.execute_script(action[c.SCRIPT_KEY])

    def switch_window_handle(self, action, element):
        index = action.get(c.INDEX_KEY)
        if index is not None:
            handles = self.sh.get_window_handles()
            self.sh.switch_window_handle(handles[index])
        else:
            self.sh.switch_window_handle()

    def switch_to_iframe(self, action, element):
        if action.get(c.DEFAULT_CONTENT_KEY):
            self.sh.driver.switch_to_default_content()
        else:
            self.sh.driver.switch_to_frame(self.sh.get_element(action[c.CSS_SELECTOR_KEY]))

    def add_cookie(self, action, element):
        name = action[c.NAME_KEY].replace("<domain>", c.parse_domain(self.sh.get_current_url()))
        self.sh.add_cookie(name, action[c.VALUE_KEY])

    def delete_cookie(self, action, element):
        name = action[c.NAME_KEY].replace("<domain>", c.parse_domain(self.sh.get_current_url()))
        self.sh.delete_cookie(name)

    def close_window(self, action, element):
        self.sh.close_window()

    def focus(self, action, element):
        self.sh.execute_script('alert(1);')
        alert = self.sh.driver.switch_to_alert()
        alert.accept()

    def external(self, action, element):
        references = action[c.REFERENCE_KEY]
        if isinstance(references, list):
            for reference in references:
                self.t.dispatch_external_reference(action, reference)
        else:
            self.t.dispatch_external_reference(action, references)

    def for_each(self, action, element):
        elements = []

        # Stop the action if there are no elements that match the given css selector for the action.
        if not self.sh.element_exists(action[c.CSS_SELECTOR_KEY]):
            # Get pissed if the allow_empty key is True or not given
            if not action.get(c.ALLOW_EMPTY):
                message = f"There were no elements found using the css selector '{action[c.CSS_SELECTOR_KEY]}'. Exiting the for_each action and " \
                          "continuing with the remaining actions on this page"
                raise c.HippoGeneralException(message)
        else:
            elements = self.sh.get_list_of_elements(action[c.CSS_SELECTOR_KEY])

        for element in elements:
            if not action.get(c.DO_NOT_INCREMENT_KEY):
                self.iteration += 1
            self.t.dispatch_actions(action[c.ACTION_LIST_KEY], element=element)

        if not action.get(c.CHILD_KEY):
            self.iteration = 0

    def resize_browser(self, action, element):
        # Setting the width to what was passed through, otherwise use the default width set in the config.
        width = action.get(c.WIDTH_KEY, self.t.browser_size[c.WIDTH_KEY])

        # Get into the below block if the browser needs to be as tall as the content on the page.
        if action.get(c.CONTENT_HEIGHT_KEY):
            # Get the maximum height and the padding based on the browser being used.
            head_padding = FIREFOX_HEAD_HEIGHT if self.sh.desired_capabilities["browserName"] == "firefox" else 0
            content_height = self.sh.get_content_height(
                action.get(c.CSS_SELECTOR_KEY, self.t.content_container_selector))
            height = content_height + head_padding
        else:
            height = action.get(c.HEIGHT_KEY, self.t.browser_size[c.HEIGHT_KEY])

        # Pass the height and width into the Selenium Helper action to resize the browser
        self.sh.resize_browser(width, height)
