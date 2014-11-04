require 'sinatra'
require 'yaml'
require 'json'
require 'yahoo_weatherman'
require 'google_directions'
require 'wolfram-alpha'
require 'mechanize'

configure do
  set :conf, YAML.load_file('config.yml') rescue nil || {}
  set :bind, '0.0.0.0'
  set :logging, true
end

before do
  content_type :json
end

helpers do
  def capitalize(input_string)
    input_string.split.map(&:capitalize).join(' ')
  end
  def strip_it(input_string)
    input_string.gsub(/([\n|\t])|(\&nbsp;?){1,}/, '').gsub(/(\s)/, ' ').strip
  end
  def initial_check(input_string)
    wolfram_pods = ['Result', 'Response', 'Basic information', 'Definition', 'Current result', 'Population']
    return true if wolfram_pods.include? input_string
  end
  def final_check(input_string)
    wolfram_pods = ['Input interpretation', 'Ernie']
    return true if wolfram_pods.include? input_string
  end
end

get '/' do
  'Welcome to Ernie!'
end

get '/weather/:location' do
  halt 400, 'Missing param' unless params[:location]
  location = params[:location]
  client = Weatherman::Client.new
  response = client.lookup_by_location("#{location}")
  halt 404, 'Not found' if response.description.include? 'Invalid Input'
  # IMPROVE - ugh ugly codes
  temp = response.condition['temp'] || ''
  desc = response.condition['text'] || ''
  day = params[:day] ? params[:day] : 0
  halt 404, 'Day of weather too advanced' if response.forecasts[day.to_i].nil?
  forecast = response.forecasts[day.to_i]['text']
  reply = day==0 ? "#{temp}C and #{desc} today}" : "#{forecast} on #{response.forecasts[day.to_i]['day']}"
  result = {
    reply: reply
  }
  result.to_json
end

get '/goto/:origin/:destination' do
  halt 400, 'Missing param' unless params[:destination]
  origin = params[:origin]
  destination = params[:destination]
  # TODO If params origin is missing, just give back the "address"
  directions = GoogleDirections.new(origin, destination)
  halt 404, "Not found #{directions.status}" if directions.status != 'OK'
  result = {
    distance: directions.distance_text,
    time: directions.drive_time_in_minutes,
    reply: directions.steps.join(" ").gsub(/<[^>]*>/ui, '').gsub(/"|'/, ''),
    size: directions.steps.size }
  result.to_json
end

get '/traffic/:location' do
  halt 400, 'Missing param' unless params[:location]
  location = params[:location].split.map(&:capitalize).join(' ')
  mechanize = Mechanize.new
  situation = []
  last_update = ''
  road_lines = settings.conf['mmda']
  road_lines.each do |road_line|
    page = mechanize.get(road_line)
    situation = page.search("div.line-table > div:contains('#{location}') > div.line-col > div.line-status > div:nth-child(2)")
    last_update = page.search("div.line-table > div:contains('#{location}') > div.line-col > p")
    break unless situation.empty?
  end
  halt 404, 'Not found' if situation.empty?
  last_update = last_update.last.text unless last_update.empty?
  result = {
    query: location,
    sb_situation: situation[0].text,
    nb_situation: situation[1].text,
    last_update: last_update,
    reply: "SB: #{situation[0].text} NB: #{situation[1].text} #{last_update}" }
  result.to_json
end

# TODO
get '/movie/:sched' do
  halt 418, 'Teapot!'
end

get '/any' do
  halt 500, 'Missing config' if settings.conf['api']['wolfram_key'].nil?
  halt 400, 'Missing param' unless params[:query]
  request_query = params[:query]
  options = { format: 'plaintext' }
  client = WolframAlpha::Client.new settings.conf['api']['wolfram_key'], options
  response = client.query "#{request_query}"
  input = response['Input'] # Get the input interpretation pod.
  # OPTIMIZE - needs improvement in checking pods
  result = response.find { |pod| initial_check(pod.title) } # Get the result pods
  result = response.find { |pod| final_check(pod.title) } if result.nil? # Get the other pods
  halt 404, 'Not found' if result.nil?
  result = {
    query: input.subpods[0].plaintext,
    reply: result.subpods[0].plaintext }
  result.to_json
end


