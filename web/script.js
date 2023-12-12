setup_one_button = document.querySelector("#setup-screen-one .next");
setup_one_field = document.querySelector("#setup-screen-one .path-input");
setup_one_button.addEventListener("click", function () {
    const file = document.querySelector("#setup-screen-one .file-input").files[0];
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.addEventListener("load", function () {
        const image_base64 = reader.result;
        document.querySelector("#setup-screen-one").style.display = "none";
        document.querySelector("#setup-screen-two").style.display = "block";

        step_two_image = document.querySelector("#setup-screen-two .image");
        step_two_crop_box = document.querySelector("#setup-screen-two .crop-box");
        step_two_image.src = image_base64;
        step_two_image.addEventListener("load", function () {
            const starting_width = Math.min(step_two_image.width, step_two_image.height);
            step_two_crop_box.style.width = starting_width + "px";
            step_two_crop_box.style.height = starting_width + "px";
            step_two_crop_box.style.top = "0px";
            step_two_crop_box.style.left = "0px";
        });

        step_two_button = document.querySelector("#setup-screen-two .next");
        resize_handle = document.querySelector("#setup-screen-two .handle");

        let resizing = false;
        resize_handle.addEventListener("mousedown", function (e) {
            e.preventDefault();
            resizing = true;
            window.addEventListener("mousemove", resize_box);
            window.addEventListener("mouseup", stop_resize_box);
        });

        function resize_box(e) {
            e.preventDefault();
            const rect = step_two_image.getBoundingClientRect();
            const x = e.pageX - rect.left;
            step_two_crop_box.style.width = x - step_two_crop_box.offsetLeft + "px";
            step_two_crop_box.style.height = x - step_two_crop_box.offsetLeft + "px";
        }

        function stop_resize_box(e) {
            e.preventDefault();
            resizing = false;
            window.removeEventListener("mousemove", resize_box);
            window.removeEventListener("mouseup", stop_resize_box);
        }

        let touch_start = null;
        step_two_crop_box.addEventListener("mousedown", function (e) {
            if (resizing) {
                return;
            }
            e.preventDefault();
            touch_start = [e.pageX - step_two_crop_box.offsetLeft, e.pageY - step_two_crop_box.offsetTop];
            window.addEventListener("mousemove", move_box);
            window.addEventListener("mouseup", stop_move_box);
        })

        function move_box(e) {
            e.preventDefault();
            step_two_crop_box.style.top = e.pageY - touch_start[1] + "px";
            step_two_crop_box.style.left = e.pageX - touch_start[0] + "px";
        }

        function stop_move_box(e) {
            e.preventDefault();
            window.removeEventListener("mousemove", move_box);
            window.removeEventListener("mouseup", stop_move_box);
        }

        step_two_button.addEventListener("click", function () {
            console.log("click step two button")
            const crop_box = document.querySelector("#setup-screen-two .crop-box");
            const crop_box_rect = crop_box.getBoundingClientRect();
            const image_rect = step_two_image.getBoundingClientRect();
            const crop = [
                (crop_box_rect.left - image_rect.left) / step_two_image.width,
                (crop_box_rect.top - image_rect.top) / step_two_image.height,
                crop_box_rect.width / step_two_image.width,
                crop_box_rect.height / step_two_image.height
            ]
            eel.set_image(image_base64, crop)
            document.querySelector("#setup-screen-two").style.display = "none";
            document.querySelector("#render-screen").style.display = "block";

            const update_render = function () {
                const ret = eel.render()();
                ret.then(function (image_base64) {
                    document.querySelector("#render-screen img").src = image_base64;
                })
            }

            document.addEventListener("keydown", function (e) {
                if (e.key == "w" || e.key == "ArrowUp") {
                    eel.move_camera("w");
                } else if (e.key == "a" || e.key == "ArrowLeft") {
                    eel.move_camera("a");
                } else if (e.key == "s" || e.key == "ArrowDown") {
                    eel.move_camera("s");
                } else if (e.key == "d" || e.key == "ArrowRight") {
                    eel.move_camera("d");
                }

                update_render();
            })

            update_render();
        });
        
    });
});
