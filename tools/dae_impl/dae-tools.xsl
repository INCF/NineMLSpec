<?xml version="1.0" encoding="iso-8859-1"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <html>
      <head>
        <link rel="stylesheet" href="dae-tools.css" type="text/css" media="all" />
        <title>
            DAE Tools (www.daetools.com) Model Report: <xsl:value-of select="Model/Name"/>
        </title>

      </head>
      <body>
        <div id="wrap">
<!--
        <div id="header">
            <div id="header-content">
                <h1 id="logo">
                    <a href="index.html" title="">
                        DAE Tools<span class="gray">Project</span>
                    </a>
                </h1>
                <h2 id="slogan">Model the world freely...</h2>
            </div>
        </div>
        <div id="header-line">
        </div>
-->

        <div id="content-wrap">
        <div id="content">
<!--
        <div id="sidebar">
            <div class="sidebox">
                <ul class="sidemenu">
                    <li><a href="#ChildModels">Child Models</a></li>
                    <li><a href="#Ports">Ports</a></li>
                    <li><a href="#Domains" class="top">Domains</a></li>
                    <li><a href="#Parameters">Parameters</a></li>
                    <li><a href="#Variables">Variables</a></li>
                    <li><a href="#Equations">Equations</a></li>
                    <li><a href="#STNs">State Transition Networks</a></li>
                </ul>
            </div>
        </div>
-->
        <div id="main">

        
          <div class="post">

            <h1>
                <a class="dae-tools-project" href="http://www.daetools.com">
                    DAE Tools<span class="gray"> Project,</span> www.daetools.com
                </a>
            </h1>

            <h1 style="text-align: center;">
                Model: <xsl:copy-of select="Model/Name"/> 
            </h1>

            <xsl:if test="Model/Description != ''">
                <pre>
                    <xsl:value-of select="Model/Description"/>
                </pre>
            </xsl:if>

            <xsl:apply-templates select="Model/Units"/>
            <xsl:apply-templates select="Model/Ports"/>
            <xsl:apply-templates select="Model/EventPorts"/>
            <xsl:apply-templates select="Model/PortConnections"/>
            <xsl:apply-templates select="Model/EventPortConnections"/>
            <xsl:apply-templates select="Model/Domains"/>
            <xsl:apply-templates select="Model/Parameters"/>
            <xsl:apply-templates select="Model/Variables"/>
            <xsl:if test="count(Model/Equations/Object) > 0">
                <h2><a name="Equations"></a>Equations</h2>
                <xsl:apply-templates select="Model/Equations"/>
            </xsl:if>

            <xsl:if test="count(Model/STNs/Object) > 0">
                <h2> <a name="STNs"></a>State Transition Networks</h2>
                <xsl:apply-templates select="Model/STNs"/>
            </xsl:if>

            <xsl:if test="count(Model/OnEventActions/Object) > 0">
                <h2><a name="OnEventActions"></a>OnEventActions</h2>
                <xsl:apply-templates select="Model/OnEventActions"/>
            </xsl:if>

        </div>

        </div> <!-- main -->

      </div> <!-- wrap -->

      </div> <!-- content -->
      </div> <!-- content-wrap -->

      </body>
    </html>
  </xsl:template>



  <xsl:template match="Domains">
    <div>
      <xsl:if test="count(Object) > 0">

        <h2> <a name="Domains"></a>Domains</h2>

        <table class="width100pc">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Units</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <xsl:for-each select="Object">
              <tr>
                <td>
                  <a>
                    <xsl:attribute name="name">
                      <xsl:value-of select="@ID"/>
                    </xsl:attribute>
                    <!--<xsl:value-of select="Name"/>-->
                    <xsl:copy-of select="MathMLName"/> 
                  </a>
                </td>

                <td>
                    <xsl:if test="Type = 'eDistributed'">
                        Distributed
                    </xsl:if>
                    <xsl:if test="Type = 'eArray'">
                        Array
                    </xsl:if>
                    <!--<xsl:value-of select="Type"/>-->
                </td>

                <td>
                    <xsl:value-of select="Units"/>
                </td>
                
                <td>
                  <xsl:value-of select="Description"/>
                </td>

              </tr>
            </xsl:for-each>
          </tbody>
        </table>

      </xsl:if>
    </div>
  </xsl:template>


  <xsl:template match="DomainRefs">
    <xsl:for-each select="./ObjectRef">

      <a>
        <xsl:attribute name="href">
          #<xsl:value-of select="@ID"/>
        </xsl:attribute>
        <!--<xsl:value-of select="."/>-->
        <xsl:copy-of select="ObjectRefMathML"/> 
      </a>

      <xsl:if test="not(position() = last())">
        <xsl:text>, </xsl:text>
      </xsl:if>

    </xsl:for-each>
  </xsl:template>



  <xsl:template match="Parameters">
    <div>
      <xsl:if test="count(Object) > 0">

      <h2> <a name="Parameters"></a>Parameters</h2>

      <table class="width100pc">
        <thead>
          <tr>
            <th align="left">Name</th>
            <th align="left">Units</th>
            <th align="left">Domains</th>
            <th align="left">Description</th>
          </tr>
        </thead>
        <tbody>
          <xsl:for-each select="Object">
            <tr>
              <td align="left">
                <!-- <xsl:value-of select="Name"/>-->
                 <xsl:copy-of select="MathMLName"/>
              </td>

              <td align="left">
                 <xsl:value-of select="Units"/>
              </td>

              <td align="left">
                <xsl:apply-templates select="DomainRefs"/>
              </td>

              <td>
                  <xsl:value-of select="Description"/>
              </td>

            </tr>
          </xsl:for-each>
        </tbody>
      </table>

      </xsl:if>
    </div>
  </xsl:template>



  <xsl:template match="Variables">
    <div>
      <xsl:if test="count(Object) > 0">

      <h2> <a name="Variables"></a>Variables</h2>

      <table class="width100pc">
        <thead>
          <tr>
            <th align="left">Name</th>
            <th align="left">Type</th>
            <th align="left">Domains</th>
            <th align="left">Description</th>
          </tr>
        </thead>
        <tbody>
          <xsl:for-each select="Object">
            <tr>
              <td align="left">
                 <!--<xsl:value-of select="Name"/>-->
                 <xsl:copy-of select="MathMLName"/>
              </td>

              <td align="left">
                <xsl:value-of select="VariableType"/>
              </td>

              <td align="left">
                <xsl:apply-templates select="DomainRefs"/>
              </td>

              <td>
                  <xsl:value-of select="Description"/>
              </td>

            </tr>
          </xsl:for-each>
        </tbody>
      </table>

      </xsl:if>
    </div>
  </xsl:template>


  <xsl:template match="Units">
    <div>
        <xsl:if test="count(Object) > 0">

            <h2> <a name="Units"></a>Units</h2>

<!--            <xsl:for-each select="Object">
                <p>
                    <b>
                        <xsl:copy-of select="MathMLName"/> 
                    </b>
                    <br></br>
                    
                    <i>     
                        <xsl:value-of select="Description"/>
                    </i>
                </p>
            </xsl:for-each>
-->

            <table class="width100pc">
                <thead>
                    <tr>
                        <th align="left">Name</th>
                        <th align="left">Description</th>
                    </tr>
                </thead>
                <tbody>
                    <xsl:for-each select="Object">
                        <tr>
                            <td align="left">
                                <xsl:copy-of select="MathMLName"/>
                            </td>
                            <td align="left">
                                <xsl:value-of select="Description"/>
                            </td>
                        </tr>
                    </xsl:for-each>
                </tbody>
            </table>

       </xsl:if>
    </div>
  </xsl:template>


  <xsl:template match="Ports">
    <div>
        <xsl:if test="count(Object) > 0">
            <h2> <a name="Ports"></a>Ports</h2>

<!--
            <xsl:for-each select="Object">
                <p>
                    <b>
                        <xsl:value-of select="Name"/>:<xsl:value-of select="PortType"/>
                    </b>
                </p>
            </xsl:for-each>
-->

            <table class="width100pc">
                <thead>
                    <tr>
                        <th align="left">Name</th>
                        <th align="left">Type</th>
                        <th align="left">Description</th>
                    </tr>
                </thead>
                <tbody>
                    <xsl:for-each select="Object">
                        <tr>
                            <td align="left">
                                <!--<xsl:value-of select="Name"/>-->
                                <i>  
                                    <xsl:copy-of select="MathMLName"/> 
                                </i>
                            </td>

                            <td align="left">
                                <xsl:value-of select="PortType"/>
                            </td>

                            <td>     
                                <xsl:value-of select="Description"/>
                            </td>
                        </tr>
                    </xsl:for-each>
                </tbody>
            </table>

       </xsl:if>
    </div>
  </xsl:template>

  <xsl:template match="EventPorts">
    <div>
        <xsl:if test="count(Object) > 0">
            <h2> <a name="EventPorts"></a>EventPorts</h2>

<!--
            <xsl:for-each select="Object">
                <p>
                    <b>
                        <xsl:value-of select="Name"/>:<xsl:value-of select="PortType"/>
                    </b>
                </p>
            </xsl:for-each>
-->

            <table class="width100pc">
                <thead>
                    <tr>
                        <th align="left">Name</th>
                        <th align="left">Type</th>
                        <th align="left">Description</th>
                    </tr>
                </thead>
                <tbody>
                    <xsl:for-each select="Object">
                        <tr>
                            <td align="left">
                                <!--<xsl:value-of select="Name"/>-->
                                <i>
                                    <xsl:copy-of select="MathMLName"/>
                                </i>
                            </td>

                            <td align="left">
                                <xsl:value-of select="PortType"/>
                            </td>

                            <td>
                                <xsl:value-of select="Description"/>
                            </td>
                        </tr>
                    </xsl:for-each>
                </tbody>
            </table>

       </xsl:if>
    </div>
  </xsl:template>

  <xsl:template match="PortConnections">
    <div>
        <xsl:if test="count(Object) > 0">
            <h2> <a name="PortConnections"></a>Port Connections</h2>

<!--
            <xsl:for-each select="Object">
                <p>
                    <b>
                        <xsl:value-of select="Name"/>:<xsl:value-of select="PortType"/>
                    </b>
                </p>
            </xsl:for-each>
-->

            <table class="width100pc">
                <thead>
                    <tr>
                        <th align="left">Port 1</th>
                        <th align="left">Port 2</th>
                        <th align="left">Description</th>
                    </tr>
                </thead>
                <tbody>
                    <xsl:for-each select="Object">
                        <tr>
                            <td align="left">
                                <!--<xsl:value-of select="Name"/>-->
                                <i>  
                                    <xsl:copy-of select="PortFrom/ObjectRefMathML"/> 
                                </i>
                            </td>

                            <td align="left">
                                <!--<xsl:value-of select="Name"/>-->
                                <i>  
                                    <xsl:copy-of select="PortTo/ObjectRefMathML"/> 
                                </i>
                            </td>

                            <td>     
                                <xsl:value-of select="Description"/>
                            </td>
                        </tr>
                    </xsl:for-each>
                </tbody>
            </table>

       </xsl:if>
    </div>
  </xsl:template>

  <xsl:template match="EventPortConnections">
    <div>
        <xsl:if test="count(Object) > 0">
            <h2> <a name="EventPortConnections"></a>Event-Port Connections</h2>

<!--
            <xsl:for-each select="Object">
                <p>
                    <b>
                        <xsl:value-of select="Name"/>:<xsl:value-of select="PortType"/>
                    </b>
                </p>
            </xsl:for-each>
-->

            <table class="width100pc">
                <thead>
                    <tr>
                        <th align="left">Port 1</th>
                        <th align="left">Port 2</th>
                        <th align="left">Description</th>
                    </tr>
                </thead>
                <tbody>
                    <xsl:for-each select="Object">
                        <tr>
                            <td align="left">
                                <!--<xsl:value-of select="Name"/>-->
                                <i>
                                    <xsl:copy-of select="PortFrom/ObjectRefMathML"/>
                                </i>
                            </td>

                            <td align="left">
                                <!--<xsl:value-of select="Name"/>-->
                                <i>
                                    <xsl:copy-of select="PortTo/ObjectRefMathML"/>
                                </i>
                            </td>

                            <td>
                                <xsl:value-of select="Description"/>
                            </td>
                        </tr>
                    </xsl:for-each>
                </tbody>
            </table>

       </xsl:if>
    </div>
  </xsl:template>

  <xsl:template match="Equations">
    <div>
      <xsl:if test="count(Object) > 0">

          <xsl:for-each select="Object">
              <p>
                <b><i>
                    <!--<xsl:value-of select="Name"/>-->
                    <xsl:copy-of select="MathMLName"/>:
                </i></b>
              </p>

              <p style="padding-left:20px">
                 <xsl:copy-of select="MathML"/>
                 <br></br>
                
                 <i>     
                    <xsl:value-of select="Description"/>
                 </i>
             </p>
          </xsl:for-each>

      </xsl:if>
    </div>
  </xsl:template>



  <xsl:template match="DistributedDomainInfos">
    <table>
      <tr>
        <th align="left">Domain</th>
        <th align="left">Type</th>
      </tr>
      <xsl:for-each select="Object">
        <tr>
          <td align="left">
            <a>
              <xsl:attribute name="href">
                #<xsl:value-of select="@ID"/>
              </xsl:attribute>
              <!--<xsl:value-of select="Domain"/>-->
              <xsl:copy-of select="MathMLName"/> 
            </a>
          </td>
          <td align="left">
            <xsl:value-of select="Type"/>
          </td>
        </tr>
      </xsl:for-each>
    </table>
  </xsl:template>



  <xsl:template match="STNs">
    <div>
      <xsl:for-each select="Object">

        <xsl:if test="Type = 'eIF'">

          <div style="padding-left:30px; padding-right:30px;">
            <h3>
               <!--<xsl:value-of select="Name"/>-->
               <xsl:copy-of select="MathMLName"/> 
            </h3>
            <p>
                <i>     
                    <xsl:value-of select="Description"/>
                </i>
            </p>

            <ul>
                <xsl:for-each select="States/Object">
                    <li>
                        <xsl:if test="count(StateTransitions/Object) = 0">
                            Else
                        </xsl:if>

                        <xsl:if test="count(StateTransitions/Object) > 0">
                            <xsl:for-each select="StateTransitions/Object">
                                If <xsl:apply-templates select="Condition"/>
                            </xsl:for-each>
                        </xsl:if>
                        <br></br>

                        <div style="padding-left:30px; padding-right:30px;">
                            <xsl:apply-templates select="Equations"/>
                            <xsl:apply-templates select="STNs"/>
                        </div>
                    </li>
                    <br/>
                </xsl:for-each>
            </ul>

          </div>
        </xsl:if>

        <xsl:if test="Type = 'eSTN'">
          <div style="padding-left:30px; padding-right:30px;">
            <h3>
               <!--<xsl:value-of select="Name"/>-->
               <xsl:copy-of select="MathMLName"/> 
            </h3>
            <p>
                <i>     
                    <xsl:value-of select="Description"/>
                </i>
            </p>

            <ul>
                <xsl:for-each select="States/Object">

                    <li>
                        <b>
                            <!--<xsl:value-of select="Name"/>-->
                            <xsl:copy-of select="MathMLName"/> 
                        </b>
                        <br></br>

                        <div style="padding-left:30px; padding-right:30px;">
                            <xsl:apply-templates select="Equations"/>
                            <xsl:apply-templates select="StateTransitions"/>
                            <xsl:apply-templates select="OnEventActions"/>
                            <xsl:apply-templates select="STNs"/>
                        </div>
                    </li>
                    <br/>

                </xsl:for-each>
            </ul>

          </div>
        </xsl:if>

      </xsl:for-each>
    </div>
  </xsl:template>



  <xsl:template match="States">
    <div>
      <xsl:for-each select="Object">
        <a>
          <xsl:attribute name="name">
            <xsl:value-of select="@ID"/>
          </xsl:attribute>
          <!--<xsl:value-of select="Name"/>-->
          <xsl:copy-of select="MathMLName"/> 
        </a>
        <xsl:apply-templates select="Equations"/>
        <xsl:apply-templates select="StateTransitions"/>
        <xsl:apply-templates select="STNs"/>
        <xsl:apply-templates select="OnEventActions"/>
      </xsl:for-each>
    </div>
  </xsl:template>

   <xsl:template match="Actions">
        <xsl:if test="count(Object) > 0">
            <ul>
                <xsl:for-each select="Object">
                    <li>
                        <xsl:if test="Type = 'eChangeState'">
                            Switch to: <xsl:copy-of select="StateTo/ObjectRefMathML"/>
                        </xsl:if>
                        <xsl:if test="Type = 'eSendEvent'">
                            Trigger the event on: <xsl:copy-of select="SendEventPort/ObjectRefMathML"/> with the data: <xsl:copy-of select="MathML"/>
                        </xsl:if>
                        <xsl:if test="Type = 'eReAssignOrReInitializeVariable'">
                            Set: <xsl:copy-of select="MathML"/>
                        </xsl:if>
                    </li>
                </xsl:for-each>
            </ul>
        </xsl:if>
  </xsl:template>


  <xsl:template match="StateTransitions">
    <div>
      <xsl:for-each select="Object">
        <p>
            If <xsl:apply-templates select="Condition"/> is satisfied: <br/>
            <xsl:apply-templates select="Actions"/>
        </p>
      </xsl:for-each>
    </div>
  </xsl:template>

  <xsl:template match="OnEventActions">
    <div>
      <xsl:for-each select="Object">
        <p>
            On event received on: <xsl:apply-templates select="EventPort/ObjectRefMathML"/> <br/>
            <xsl:apply-templates select="Actions"/>
        </p>
      </xsl:for-each>
    </div>
  </xsl:template>

  <xsl:template match="Condition">
    <xsl:text>( </xsl:text>
        <xsl:copy-of select="MathML"/>
    <xsl:text> )</xsl:text>
  </xsl:template>

</xsl:stylesheet>
