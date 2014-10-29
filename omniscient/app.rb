require 'sinatra'
require 'yaml'
require 'json'
require 'yahoo_weatherman'
require 'google_directions'
require 'wolfram-alpha'

configure do
  set :conf, YAML.load_file('config.yml') rescue nil || {}
  set :bind, '0.0.0.0'
end

helpers do
  def json_status(code, reason)
    status code
    {
      status: code,
      reason: reason
    }.to_json
  end

  def accept_params(params, *fields)
    h = {}
    fields.each do |name|
      h[name] = params[name] if params[name]
    end
    h
  end
end

get '/' do
  'Welcome to Ernie!'
end

get '/weather/:location' do
  return json_status 400, 'Missing param' unless params[:location]
  content_type :json
  location = params[:location]
  result = []
  # hsh.each_pair{ |k,v| puts "#{k}: #{v}"}
  client = Weatherman::Client.new
  response = client.lookup_by_location("#{location}")
  if response.description.include? 'Invalid Input'
    return json_status 404, 'Not found'
  end
  result = {
    temp: response.condition['temp'] || '',
    desc: response.condition['text'] || '',
    forecast: response.forecasts[2]['text'] || ''
  }
  result.to_json
end

get '/goto/:origin/:destination' do
  return json_status 400, 'Missing param' unless params[:destination]
  content_type :json
  origin = params[:origin]
  destination = params[:destination]
  # If params origin is missing, just give back the "address"
  directions = GoogleDirections.new(origin, destination)
  if directions.status != 'OK'
    return json_status 404, 'Not found'
  end
  result = {
    distance: directions.distance_text,
    time: directions.drive_time_in_minutes,
    steps: directions.steps.to_s.gsub(/<[^>]*>/ui, '').gsub(/"|'/, '') }
  result.to_json
end

# TODO
get '/movie/:sched' do
  return json_status 418, 'Teapot!'
end

# TODO
get '/any/:whatever' do
  return json_status 500, 'Missing config' if settings.conf['api']['wolfram_key'].nil?
  content_type :json
  whatever = params[:whatever]

  options = { format: 'plaintext' } # see the reference appendix in the documentation.[1]

  client = WolframAlpha::Client.new settings.conf['api']['wolfram_key'], options

  response = client.query "#{whatever}"
  input = response['Input'] # Get the input interpretation pod.
  puts response.inspect
  halt 400
  query_result = response.queryresult
  return json_status 500, 'API failed' if query_result.success == 'false'
  return json_status 400, 'Not found' if query_result.error == 'true'

  result = response.find { |pod| pod.title == 'Result' } # Get the result pod.
  if result.nil?
    result = response.find { |pod| pod.title == 'Basic information' }
  end
  "#{input.subpods[0].plaintext} = #{result.subpods[0].plaintext}"
end
