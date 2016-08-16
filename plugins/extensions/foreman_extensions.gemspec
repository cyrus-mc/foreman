require File.expand_path('../lib/foreman_extensions/version', __FILE__)
require 'date'

Gem::Specification.new do |s|
  s.name        = 'foreman_extensions'
  s.version     = ForemanExtensions::VERSION
  s.authors     = ['Matthew Ceroni']
  s.email       = ['matthewceroni@gmail.com']
  s.homepage    = 'https://github.com/cyrus-mc/foreman_extensions'
  s.summary     = 'Foreman Plug-In : Extensions'
  # also update locale/gemspec.rb
  s.description = 'Foreman Plug-In : Extensions'

  s.files = Dir['{public,app,config,db,lib,locale}/**/*'] + ['LICENSE', 'Rakefile', 'README.md']
  s.test_files = Dir['test/**/*']

  s.add_dependency 'deface'
  s.add_development_dependency 'rubocop'
  s.add_development_dependency 'rdoc'
end
