:VERBATIM
:extern double nineml_gsl_normal(double, double);
:extern double nineml_gsl_uniform(double, double);
:extern double nineml_gsl_binomial(double, int);
:extern double nineml_gsl_exponential(double);
:extern double nineml_gsl_poisson(double);
:ENDVERBATIM

TITLE Spiking node generated from the 9ML file $input_filename using 9ml2nmodl.py version $version

NEURON {
    POINT_PROCESS $component.name
    RANGE regime

    :StateVariables:
  #for sv in $component.state_variables
    RANGE $sv.name
  #end for

    :Parameters
  #for p in $component.parameters
    RANGE $p.name
  #end for

    :Aliases
  #for alias in $component.aliases
    RANGE $alias.lhs
  #end for
}

CONSTANT {
    SPIKE = 0
    INIT = 1

  #for regime in $component.regimes
    $regime.label = $regime.flag
  #end for

  #for i,channel in enumerate($channels):
    $channel = $i
  #end for

  #for transition in $component.transitions
    $transition.label = $transition.flag
  #end for
}

INITIAL {
    : Initialise State Variables:
  #for var in $component.state_variables:
    $var.name = 0
  #end for

    : Initialise Regime:
    regime = $initial_regime

    : Initialise the NET_RECEIVE block:
    net_send(0, INIT)

    first_round_fired = 0
}

PARAMETER {
  #for p in $component.parameters
    $p.name = 0
  #end for
}

STATE {
  #for var in $component.state_variables
    $var.name
  #end for
    first_round_fired
}

ASSIGNED {
    regime

  #for alias in $component.aliases:
    $alias.lhs
  #end for
  #for var in $weight_variables.values:
    $var
  #end for
}

BREAKPOINT {
    :SOLVE states METHOD derivimplicit
    SOLVE states METHOD cnexp

  #for alias in $component.aliases
    $alias.lhs = $alias.rhs
  #end for
}

DERIVATIVE states {
  #for var in $component.state_variables
    $var.name' = deriv_${var.name}($deriv_func_args($component, $var.name))
  #end for
}

#for var in $component.state_variables
FUNCTION deriv_${var.name}($deriv_func_args($component, $var.name)) {
  #for regime in $component.regimes
    if (regime== $regime.label ) {
        deriv_${var.name} = $ode_for($regime, $var).rhs
    }
  #end for
}
#end for

NET_RECEIVE(w, channel) {

    :printf("Received event with weight %f on channel %f at %f\n", w, channel, t)
    :printf("Received event at %f\n", t)

    INITIAL {
      : stop channel being set to 0 by default
    }

    if (flag == INIT) {
    #for regime in $component.regimes
      #for transition in $regime.on_conditions
        :WATCH ( $transition.trigger.rhs.replace('=','') )  4000
        WATCH ( $transition.trigger.rhs.replace('=','') )  $transition.flag
      #end for
    #end for
    } else if (flag == SPIKE) {
        :printf("Received spike with weight %f on channel %f at %f\n", w, channel, t)
      #for regime in $component.regimes
        if (regime == $regime.label) {
        :printf("Current regime: $regime.label \n")
          #for on_event in $regime.on_events
            #set channel = $get_on_event_channel($on_event,$component)
            if (channel == $channel) {
                :printf("  Resolved to channel $channel\n" )
              #if $weight_variables
                $get_weight_variable($channel, $weight_variables) = w
              #end if

              #for sa in $on_event.state_assignments
                $sa.lhs  =  $sa.neuron_rhs
              #end for

              #for node in $on_event.event_outputs
                $as_expr(node)
              #end for
            }
          #end for
        }
      #end for
    }

    : First Round of event filtering:
    : Pick up events emitted by WATCH Block.
    : Re-validate them against Conditions and Regime:
    : Retransmit the correct Transition ID

    else if (flag == 4000) {
        if(first_round_fired == 1) {

      #for $regime in $component.regimes:
        } else if( regime == $regime.flag ) {
          #for transition in $regime.on_conditions:
            if( $transition.trigger.rhs ) {
                :printf("\nFirst Round Transition Filtering: Forwarding Event: $transition.flag @ t=%f",t)
                net_send(0, $transition.flag )
            }
          #end for
      #end for
        }

        : Make sure that we only enter this block once
        first_round_fired = 1
    }

    : Second Round
  #for regime in $component.regimes:
   #for transition in $regime.on_conditions:
    else if (flag == $transition.flag) {
        first_round_fired = 0
        :printf("\nt=%f In Regime $regime.name Event With Flag: %f", t, flag )
        :printf("\nt=%f Changing Regime from $regime.name to $transition.target_regime.name via $transition.flag", t )
        regime = $transition.target_regime.flag

      #for node in $transition.event_outputs
        net_event(t)
      #end for

      #for sa in transition.state_assignments
        $sa.lhs  = $sa.neuron_rhs
      #end for
    }
   #end for
  #end for
}
