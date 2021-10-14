#define DIR_TYPE metalib

#begin metalib_target
  #define TARGET toontown
  #define COMPONENT_LIBS pets dnaLoader toontownbase suit
  #define SOURCES toontown.cxx
  #if $[BUILD_COMPONENTS]
    #define BUILDING_DLL BUILDING_TOONTOWN_STUB
  #else
    #define BUILDING_DLL BUILDING_TOONTOWN
  #endif
#end metalib_target
