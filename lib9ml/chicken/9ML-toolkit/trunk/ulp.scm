;
;;  NineML user layer processor.
;;
;;
;; Copyright 2010-2012 Ivan Raikov and the Okinawa Institute of
;; Science and Technology.
;;
;; This program is free software: you can redistribute it and/or
;; modify it under the terms of the GNU General Public License as
;; published by the Free Software Foundation, either version 3 of the
;; License, or (at your option) any later version.
;;
;; This program is distributed in the hope that it will be useful, but
;; WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
;; General Public License for more details.
;;
;; A full copy of the GPL license can be found at
;; <http://www.gnu.org/licenses/>.
;;


(require-extension extras posix utils files data-structures tcp srfi-1 srfi-13 irregex)
(require-extension datatype matchable static-modules miniML miniMLsyntax miniMLvalue miniMLeval)
(require-extension signal-diagram ssax sxml-transforms sxpath sxpath-lolevel object-graph uri-generic getopt-long )
(require-extension 9ML-parse 9ML-eval )

(define (string-match rx str)
  (and-let* ((m (irregex-match rx str)))
    (let loop ((i (irregex-match-num-submatches m))
               (res '()))
      (if (fx<= i 0)
          (cons str res)
          (loop (fx- i 1) (cons (irregex-match-substring m i) res))))))


(define lookup-def 
  (lambda (k lst . rest)
    (let-optionals rest ((default #f))
      (alist-ref k lst eq? default))))

(define (safe-car x) (and (pair? x) (car x)))

	
(include "SXML.scm")
(include "SXML-to-XML.scm")

(define-values (env-binding? env-empty env-add-signature env-add-module env-add-type env-add-spec env-add-value
	        env-find-value env-find-type env-find-module env-find)
  (make-mod-env core-syntax))

(define-values (scope-typedecl scope-modtype scope-signature scope-modterm scope-moddef)
  (make-mod-scoping core-syntax core-scoping))

(define-values (check-modtype check-signature type-modterm type-moddef type-definition)
  (make-mod-typing core-syntax core-typing))

(include "NineMLcore.scm")
(include "NineMLreal.scm")
(include "NineMLrandom.scm")
(include "NineMLsignal.scm")
(include "NineMLdiagram.scm")
(include "NineMLinterval.scm")
(include "NineMLgraph.scm")
(include "NineMLivp.scm")


(define current-scope      (make-parameter st-empty))
(define current-type-env   (make-parameter env-empty))
(define current-eval-env   (make-parameter env-empty))


(define (enter-typedecl id decl)
  (current-scope (st-enter-type id (current-scope)))
  (current-type-env   (env-add-type id decl (current-type-env))))

(define (enter-valtype name ty)
  (let ((id (ident-create name)))
    (current-scope (st-enter-value id (current-scope)))
    (current-type-env   (env-add-value id ty (current-type-env)))))

(define (enter-val name val)
  (let ((id (or (and (ident? name) name) (ident-create name))))
    (current-eval-env (ident-add id val (current-eval-env)))))

(core-initialize enter-typedecl enter-valtype)
(eval-cbv-initialize enter-val)


(define (enter-module id mty)
  (current-scope (st-enter-module id (current-scope)))
  (current-type-env (env-add-module id mty (current-type-env))))



(define opt-defaults
  `(
    ))


(define (defopt x)
  (lookup-def x opt-defaults))

(define opt-grammar
  `(

    (print-type-env  "prints the type environment of each operand"
		     (single-char #\t)
		     (value (optional COMPONENT-LIST)
			    (default all)
			    (transformer 
			     ,(lambda (x) 
				(if (string=? x "all") x
				    (list (string-split x ",")))))))

    (print-eval-env  "prints the evaluation environment of each operand"
		     (single-char #\e)
		     (value (optional COMPONENT-LIST)
			    (default all)
			    (transformer 
			     ,(lambda (x) 
				(if (string=? x "all") x
				    (list (string-split x ",")))))))

    (print-source-defs  "prints the source definitions of each operand"
			(single-char #\s))

    (output-sxml        "sets output format to SXML")

    (output-xml         "sets output format to XML")

    (platform        "simulation platform (one of chicken, chicken/cvode, mlton, octave, octave/mlton)"
		     (value (required PLATFORM)
			    (predicate 
			     ,(lambda (x) 
				(let ((s (string->symbol (string-downcase x))))
				  (case s
				    ((chicken chicken/cvode mlton octave octave/mlton) s)
				    (else (error 'ivp "unrecognized platform" x))))))
			    (transformer ,string->symbol)
			     ))

    (verbose          "print commands as they are executed"
		      (single-char #\v))

    (help  "Print help"
	    (single-char #\h))
  
  ))


;; Use args:usage to generate a formatted list of options (from OPTS),
;; suitable for embedding into help text.
(define (ulp:usage)
  (print "Usage: " (car (argv)) " file1... [options...] ")
  (newline)
  (print "Where operands are NineML user layer files")
  (newline)
  (print "The following options are recognized: ")
  (newline)
  (width 35)
  (print (parameterize ((indent 5)) (usage opt-grammar)))
  (exit 1))


;; Process arguments and collate options and arguments into OPTIONS
;; alist, and operands (filenames) into OPERANDS.  You can handle
;; options as they are processed, or afterwards.

(define opts    (getopt-long (command-line-arguments) opt-grammar))
(define opt     (make-option-dispatch opts opt-grammar))

(define ulp-verbose (make-parameter 0))
(define data-dir (make-parameter #f))
(define simulation-platform (make-parameter #f))


(define (d fstr . args)
  (let ([port (current-error-port)])
    (if (positive? (ulp-verbose)) 
	(begin (apply fprintf port fstr args)
	       (flush-output port) ) )))


(define (sxml-string->uri s) 
  (let ((ss (string-trim-both s)))
    (uri-reference ss)))


(define (get-data-dir)
  (or (opt 'data-dir)
      (or (data-dir)
	  (let ([dir (create-temporary-directory)])
	    (data-dir dir)
	    dir ) ) ))


(define (run:execute explist)
  (define (smooth lst)
    (let ((slst (map ->string lst)))
      (string-intersperse (cons (car slst) (cdr slst)) " ")))
  (for-each (lambda (cmd) (system (->string cmd)))
	    (map smooth explist)))


(define (run:execute* explist)
  (define (smooth lst)
    (let ((slst (map ->string lst)))
      (string-intersperse (cons (car slst) (cdr slst)) " ")))
  (for-each (lambda (cmd) (system* "~a" cmd))
	    (map smooth explist)))


(define-syntax run
  (syntax-rules ()
    ((_ exp ...)
     (begin
       (d "running ~A ...~%" (list `exp ...))
       (run:execute* (list `exp ...))))))


(define-syntax run-
  (syntax-rules ()
    ((_ exp ...)
     (begin
       (d "running ~A ...~%" (list `exp ...))
       (run:execute (list `exp ...))))))


(define (create-temporary-directory)
  (let ((dir (or (get-environment-variable "TMPDIR") 
		 (get-environment-variable "TEMP") 
		 (get-environment-variable "TMP") 
		 "/tmp")))
    (let loop ()
      (let* ((n (current-milliseconds))
	     (pn (make-pathname dir (string-append "9ML-ulp-" (number->string n 16)) "tmp")))
	(cond ((file-exists? pn) (loop))
	      (else (mkdir pn) pn))))))


(define (network-failure msg . args)
  (signal
   (make-composite-condition
    (make-property-condition
       'exn
       'message "invalid response from server"
       'arguments args)
    (make-property-condition 'http-fetch))) )



(define (make-HTTP-GET/1.1 location user-agent host
			   #!key
			   (port 80)
			   (connection "close")
			   (accept "*")
			   (content-length 0))
  (conc
   "GET " location " HTTP/1.1" "\r\n"
   "Connection: " connection "\r\n"
   "User-Agent: " user-agent "\r\n"
   "Accept: " accept "\r\n"
   "Host: " host #\: port "\r\n"
   "Content-length: " content-length "\r\n"
   "\r\n") )

(define (match-http-response rsp)
  (and (string? rsp)
       (string-match "HTTP/[0-9.]+\\s+([0-9]+)\\s+.*" rsp)) )

(define (response-match-code? mrsp code)
  (and mrsp (string=? (number->string code) (cadr mrsp))) )

(define (match-chunked-transfer-encoding ln)
  (string-match "[Tt]ransfer-[Ee]ncoding:\\s*chunked.*" ln) )


(define (http-fetch uri dest)
  (d "fetching ~s ...~%" (uri->string uri))
  (match-let (((_ ((_ host port) ('/ . path) query) _) (uri->list uri)))
    (let* ((port      (or port 80))
	   (locn      (uri->string (update-uri (update-uri uri scheme: #f) host: #f)))
	   (query     (and query (not (string-null? query)) query))
	   (filedir   (uri-decode-string (string-concatenate (intersperse (if query path (drop-right path 1)) "/"))))
	   (filename  (uri-decode-string (or (and query (cadr (string-split query "="))) (last path))))
	   (dest      (make-pathname dest filedir))
	   (filepath  (make-pathname dest filename)))
      (if (file-exists? filepath) filepath
	  (begin
	  (d "connecting to host ~s, port ~a ...~%" host port)
	  (let-values ([(in out) (tcp-connect host port)])
		      (d "requesting ~s ...~%" locn)
		      (display
		       (make-HTTP-GET/1.1 locn "NineML" host port: port accept: "*/*")
		       out)
		      (flush-output out)
		      (d "reading response ...~%")
		      (let ([chunked #f] [ok-response #f])
			(let* ([h1 (read-line in)]
			       [response-match (match-http-response h1)])
			  (d "~a~%" h1)
			  ;;*** handle redirects here
			  (cond ((response-match-code? response-match 200)
				 (set! ok-response #t))
				((response-match-code? response-match 404)
				 (d "file not found on server: ~s~%" locn))
				(else (network-failure "invalid response from server" h1) ))
			(and ok-response
			    (begin
			      (let loop ()
				(let ([ln (read-line in)])
				  (unless (string-null? ln)
				    (when (match-chunked-transfer-encoding ln) (set! chunked #t))
				    (d "~a~%" ln)
				    (loop) ) ) )
			      (if chunked
				  (begin
				    (d "reading chunks ...~%")
				    (let ([data (read-chunks in)])
				      (close-input-port in)
				      (close-output-port out)
				      (if (not (file-exists? dest)) (mkdir dest))
				      (d "writing to ~s~%" filepath)
				      (with-output-to-file filepath (cut display data) )
				      filepath))
				  
				  (begin
				    (d "reading data ...~%")
				    (let ([data (read-string #f in)])
				      (close-input-port in)
				      (close-output-port out)
				      (if (not (file-exists? dest)) (mkdir dest))
				      (d "writing to ~s~%" filepath)
				      (with-output-to-file filepath (cut display data) binary:)
				      filepath)))))
			)
		      )))))))

  (define (read-chunks in)
    (let get-chunks ([data '()])
      (let ([size (string->number (read-line in) 16)])
	(if (zero? size)
	    (string-concatenate-reverse data)
	    (let ([chunk (read-string size in)])
	      (read-line in)
	      (get-chunks (cons chunk data)) ) ) ) ) )


(define (fetch uri)
  (case (uri-scheme uri)
    ((http)
     (let-values (((fd temp-path) (file-mkstemp "/tmp/9ML.XXXXXX")))
       (let ((data (and (http-fetch uri temp-path) (read-all temp-path))))
	 (file-close fd)
	 data)))
    ((file)
     (let ((data (read-all (string-concatenate (map ->string (uri-path uri))))))
       data))
    (else (error 'fetch "unknown scheme" (uri-scheme uri)))
    ))



(define (parse-xml str)
  (call-with-input-string str
      (lambda (in)
	(ssax:xml->sxml in `((nml . ,nineml-xmlns))))
      ))


(define (eval-source def current-scope current-type-env current-eval-env)
  (let* ((scoped-defs      (scope-moddef (current-scope) defs))
	 (mty              (type-moddef (current-type-env) '() scoped-defs))
	 (type-env         (map (lambda (x) (cases modspec x
						   (Value_sig (id vty) (cons id x))
						   (Type_sig (id decl) (cons id x))
						   (Module_sig (id mty) (cons id x))
						   )) mty))
	 (eval-env         (mod-eval-cbv (current-eval-env) scoped-defs))
	 (unified-env      (list scoped-defs
				 (filter (lambda (x) (not (assoc (car x) (current-type-env)))) type-env) 
				 (filter (lambda (x) (not (assoc (car x) (current-eval-env)))) eval-env) ))
	 
	 )
    unified-env
    ))


(define (parse-ul-component x) 

  (let ((definition ((sxpath `(// nml:definition))  x))
	(properties ((sxpath `(// nml:properties nml:quantity nml:value))  x)))

    (if (null? definition)
	(error 'parse-ul-component "component without definition" x))

    (let* ((uri  (sxml-string->uri (sxml:text (safe-car definition))))
	   (src  (fetch uri))
	   (uenv (if (not src)
		     (error 'parse-ul-component "resource not found" (uri->string uri))
		     (eval-source (parse 'parse-ul-component src) 
				  current-scope current-type-env current-eval-env)))
	   )
      
      (current-scope (car uenv))
      (current-type-env (append (cadr uenv) (current-type-env)))
      (current-eval-env (append (caddr uenv) (current-eval-env)))

      (if (null? eval-env)
	  (error 'parse-ul-component "empty definition" definition))

      (let ((last-entry-name  (car (last (caddr uenv))))
	    (property-values (map (compose string->number sxml:text) properties)))
	
	(eval-source (list (apply-terms (Longid last-entry-name) property-values))
		     current-scope current-type-env current-eval-env)	

	))
    ))


#|

TODO: use the following term rewriting rules for parse-ul-component

     ( (M component (definition $url) $properties) =>
       (M component (eval-env (M eval-definition $url)) $properties) )

     ( (M component (eval-env $eval-env) $properties) =>
       (M component (model-module (eval-env-last-entry $eval-env)) $properties) )

     ( (M component (eval-env $eval-env) $properties) =>
       (M component (model-module (eval-env-last-entry $eval-env)) $properties) )

     ( (M component (model-module $model-module) $properties) =>
       (eval-term (M apply-terms (Longid (Pdot (entry-name $model-module) "construct")) $properties)) )

     ( (M eval-definition $url ) =>
       (eval-source (fetch (uri-reference $url)) current-scope current-type-env current-eval-env ) )

     ( (M apply-terms $operator (seq $term $rest)) =>
       (M apply-terms (Apply $operator $term) $rest) )
       
     ( (M apply-terms $operator (seq-empty)) => $operator )
|#

  

(define (main options operands)

  (if (options 'help) (ulp:usage))


  (let ((find-module (lambda (x) (env-find-module x (current-type-env)))))
    (for-each (lambda (init name) (init name enter-module find-module current-eval-env))
	      (list Real:module-initialize   
		    Random:module-initialize   
		    Signal:module-initialize   
		    Diagram:module-initialize  
		    Interval:module-initialize 
		    Graph:module-initialize
		    IVP:module-initialize )
	      (list "Real" "Random" "Signal" "Diagram" "Interval" "Graph" "IVP" )) )

  (if (null? operands)
      (ulp:usage)
      (let ((output-type (cond ((options 'output-xml)  'xml)
			       ((options 'output-sxml) 'sxml)
			       (else #f))))
	(if (options 'verbose) (begin (eval-verbose 1) (ivp-verbose 1)))
	(simulation-platform (or (options 'platform) (defopt 'platform) ))
	(for-each
	 (lambda (operand)

	   (let* ((ul-sxml (parse-xml (read-all operand)))
		  (ul-imports ((sxpath `(// nml:nineml nml:import))  ul-sxml))
		  (ul-import-sxmls (map (lambda (x) (parse-xml (fetch (sxml-string->uri (sxml:text x))))) ul-imports)))

	     (let* ((ul-sxml (fold append ul-sxml ul-import-sxmls))
		    (ul-parameters ((sxpath `(// nml:nineml nml:quantity))  ul-sxml))
		    (ul-groups ((sxpath `(// nml:nineml nml:group))  ul-sxml))
		    (dd (begin (print "ul-groups = ") (pp ul-groups)))
		    
		    (ul-components ((sxpath `(// nml:nineml nml:component))  ul-sxml))
		    (ul-component-uenvs (map parse-ul-component ul-components))

		    )


	       (for-each
		(lambda (uenv) 
	       
		  (let ((source-defs (car uenv))
			(mty         (cadr uenv))
			(eval-env    (caddr uenv)))
		    
		    (let ((type-env-opt (options 'print-type-env)))
		      (if type-env-opt
			  (if (and (string? type-env-opt) (string=?  type-env-opt "all"))
			      (print-type-env mty output-type)
			      (let ((fc (lambda (x) (and (member (ident-name (car x)) type-env-opt) x))))
				(print-type-env mty output-type fc)))
			  ))
		    
		    (let ((eval-env-opt (options 'print-eval-env)))
		      (if eval-env-opt
			  (if (and (string? eval-env-opt) (string=? eval-env-opt "all"))
			      (print-eval-env eval-env output-eval)
			      (let ((fc (lambda (x) (and (member (ident-name (car x)) eval-env-opt) x))))
				(print-eval-env eval-env output-type fc)))
			  ))
		    
		    (if (options 'print-source-defs)
			(print-source-defs source-defs output-type))
		    
		    ))
		 ul-component-uenvs

		))
	     ))

	 operands))))

(main opt (opt '@))


