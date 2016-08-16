Rails.application.routes.draw do
  get 'new_action', to: 'foreman_extensions/hosts#new_action'
end
