var gulp        = require('gulp');

var browserify  = require('browserify');
var babelify    = require('babelify');
var source      = require('vinyl-source-stream');
var buffer      = require('vinyl-buffer');
var uglify      = require('gulp-uglify');
var sourcemaps  = require('gulp-sourcemaps');
var livereload  = require('gulp-livereload');


gulp.task('build', function () {
    // app.js is your main JS file with all your module inclusions
    return browserify({entries: './src/webirc/static/js/templates.js', debug: true})
        .transform("babelify", { presets: ["es2015", "react"] })
        .bundle()
        .pipe(source('templates.js'))
        .pipe(buffer())
        .pipe(sourcemaps.init())
        .pipe(uglify())
        .pipe(sourcemaps.write('./src/webirc/static/js/dist/maps'))
        .pipe(gulp.dest('./src/webirc/static/js/dist/'))
        .pipe(livereload());
});

gulp.task('watch', ['build'], function () {
    livereload.listen();
    gulp.watch('./src/webirc/static/js/*.js', ['build']);
});

gulp.task('default', ['watch']);