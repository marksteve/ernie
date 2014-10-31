require 'sinatra'
require 'yaml'
require 'json'
require 'yahoo_weatherman'
require 'google_directions'
require 'wolfram-alpha'

configure do
  set :conf, YAML.load_file('config.yml') rescue nil || {}
  set :bind, '0.0.0.0'
  set :logging, true
end

before do
  content_type :json
end

helpers do
end

get '/' do
  'Welcome to Ernie!'
end

get '/weather/:location' do
  halt 400, 'Missing param' unless params[:location]
  location = params[:location]
  result = []

  client = Weatherman::Client.new
  response = client.lookup_by_location("#{location}")
  halt 404, 'Not found' if response.description.include? 'Invalid Input'

  result = {
    temp: response.condition['temp'] || '',
    desc: response.condition['text'] || '',
    forecast: response.forecasts[2]['text'] || ''
  }
  result.to_json
end

get '/goto/:origin/:destination' do
  halt 400, 'Missing param' unless params[:destination]
  origin = params[:origin]
  destination = params[:destination]
  # TODO If params origin is missing, just give back the "address"
  directions = GoogleDirections.new(origin, destination)
  halt 404, 'Not found' if directions.status != 'OK'

  result = {
    distance: directions.distance_text,
    time: directions.drive_time_in_minutes,
    steps: directions.steps.to_s.gsub(/<[^>]*>/ui, '').gsub(/"|'/, ''),
    size: directions.steps.size }
  result.to_json
end

# TODO
get '/traffic/:location' do
  halt 418, 'Teapot!'
end

# TODO
get '/movie/:sched' do
  halt 418, 'Teapot!'
end

get '/any/:whatever' do
  halt 500, 'Missing config' if settings.conf['api']['wolfram_key'].nil?
  halt 400, 'Missing param' unless params[:whatever]
  whatever = params[:whatever]
  options = { format: 'plaintext' } # see the reference appendix in the documentation.[1]
  client = WolframAlpha::Client.new settings.conf['api']['wolfram_key'], options
  response = client.query "#{whatever}"
  input = response["Input"] # Get the input interpretation pod.
  result = response.find { |pod| pod.title == 'Result' } # Get the result pods
  halt 404, "Not found" if result.nil?
  result = {
    query: input.subpods[0].plaintext,
    answer: result.subpods[0].plaintext }
  result.to_json
end
