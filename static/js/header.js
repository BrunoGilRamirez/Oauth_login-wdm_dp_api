function header_animation(){
    var page = window.location.pathname;
    let pages = [
        {path:'/UI/home', button_id:'home'},
        {path: '/UI/access_keys', button_id:'access_keys'},
        {path: '/UI/user_settings', button_id:'user_settings'}
    ]
    pages.forEach((element) => {
        if (page === element.path){
            var button = document.getElementById(element.button_id);
            button.style.backgroundColor = "#ef7800";
            button.style.color = "white";
        }
    });
}