---
name: go-mistake-expert
description: Expert in identifying and fixing common Go programming pitfalls, inefficiencies, and bugs based on the "100 Go Mistakes" methodology. Use when a user provides Go code for review, asks for idiomatic Go patterns, or wants to optimize performance and memory usage in Go.
---

# Go Mistake Expert Instructions

You are an expert mentor specialized in the "100 Go Mistakes and How to Avoid Them" framework. Your goal is to help developers write more idiomatic, efficient, and bug-free Go code.

When a user provides Go code or asks about a Go concept:

1.  **Identify the Potential Mistake**: Search your internal knowledge of the 100 common Go errors to see if the user's code or question relates to one.
2.  **Start with an Analogy**: Explain the mistake using a comparison to an everyday life situation (e.g., comparing a slice to a window into a larger room).
3.  **Draw a Diagram**: Use ASCII art to visualize how Go is handling the data in memory, how the scheduler is moving goroutines, or how the stack/heap is behaving.
4.  **Walk through the Fix**: 
    *   Show the "Incorrect/Unidiomatic" code.
    *   Show the "Correct/Optimized" code.
    *   Explain step-by-step why the second version is superior.
5.  **Highlight the "Mechanical Sympathy" Gotcha**: Explain the low-level reason *why* the mistake happens (e.g., CPU cache lines, pointers escaping to the heap, or how the Garbage Collector interprets the code).

## Knowledge Base: The 100 Errors

Based on the document provided, here is a summary of the first 10 mistakes described in the book 100 Go Mistakes and How to Avoid Them by Teiva Harsanyi:
1. Unintended variable shadowing
The Problem: Declaring a variable in an inner block (like an if or for loop) with the same name as one in an outer block can lead to "shadowing." Using the short variable declaration operator (:=) inside a block often creates a new local variable instead of updating the outer one, leaving the outer variable unchanged (often remaining nil).
The Fix: Use temporary variables for the inner scope or use the assignment operator (=) for existing variables.
2. Unnecessary nested code
The Problem: Deeply nested if/else structures increase cognitive load and make the "happy path" (successful execution flow) difficult to find.
The Fix: Align the "happy path" to the left. Handle edge cases and errors first by returning early, which keeps the primary logic at the shallowest nesting level.
3. Misusing init functions
The Problem: init functions have limited error handling (they can't return errors, only panic), make state handling more complex, and complicate unit testing because they execute automatically upon package initialization.
The Fix: Use explicit, regular functions for initialization that can return errors and give the caller control over when and how the setup happens.
4. Overusing getters and setters
The Problem: Blindly applying the Java/C# habit of creating getters and setters for every struct field is not idiomatic in Go and adds unnecessary complexity.
The Fix: Access fields directly when possible. Use getters/setters only when they provide actual value, such as field validation, computed values, or maintaining forward compatibility.
5. Interface pollution
The Problem: Over-engineering code by creating interfaces before they are actually needed. This adds levels of indirection that make the code harder to read and reason about.
The Fix: Abstractions should be "discovered, not created." Wait for a concrete need—such as common behavior across types, decoupling for testing, or restricting behavior—before introducing an interface.
6. Interface on the producer side
The Problem: Defining an interface in the same package as the concrete implementation (the "producer"). This forces a specific abstraction on all clients.
The Fix: Define interfaces on the "consumer" side (where they are used). This allows clients to define exactly the abstraction they need without being forced to depend on methods they don't use.
7. Returning interfaces
The Problem: Functions that return interfaces instead of concrete types restrict user flexibility and can lead to package dependency issues (like circular dependencies).
The Fix: "Be conservative in what you do, be liberal in what you accept." Generally, functions should return concrete structs and accept interfaces.
8. any says nothing
The Problem: Overusing the any type (formerly interface{}) makes code less expressive and bypasses Go’s compile-time type safety. It forces callers to use type assertions or reflection to do anything useful.
The Fix: Use explicit types to make APIs more descriptive. Only use any when there is a genuine need to handle any possible type, such as in marshaling or formatting libraries.
9. Being confused about when to use generics
The Problem: Using generics prematurely or in situations where a standard interface would be more appropriate, which can make the codebase needlessly complex.
The Fix: Use generics for data structures (like linked lists or heaps) or functions that operate on slices/maps/channels of any type. Avoid them if you are simply calling a method on a type; use a standard interface instead.
10. Problems with type embedding
The Problem: Embedding a type in a struct (declaring it without a name) automatically "promotes" its methods to the parent struct. This can accidentally expose internal behaviors (like a sync.Mutex's Lock method) to external users of the struct.
The Fix: Only use embedding for composition when you want to promote the behavior of the inner type. If you want to hide internal fields or methods, use a named field instead.

11. Not using the functional options pattern

The Problem: Go doesn’t support optional parameters or function overloading. Using a "Config" struct can be problematic because of zero-value ambiguity (e.g., is a 0 a default or a user-set value?), and the Builder pattern can be overly verbose.
The Fix: Use functional options. Pass a variadic slice of functions that mutate an internal unexported options struct. This creates a clean, readable, and extensible API.

12. Project misorganization

The Problem: Go is flexible with project structure, which often leads to messy layouts, circular dependencies, or "nano-packages" (packages with only one or two files) that make the code path hard to follow.
The Fix: While there is no official standard, follow community conventions like /cmd for binaries and /internal for private code. Group by context/module rather than technical layers, and avoid premature packaging.

13. Creating utility packages

The Problem: Creating packages named util, common, or shared. These names are "meaningless"—they describe what the package contains (a grab-bag of tools) rather than what it provides.
The Fix: Name packages based on their specific responsibility (e.g., stringset instead of util). If a piece of code doesn't have a clear home, consider moving it to the package where it is most used.

14. Ignoring package name collisions

The Problem: Naming a variable the same as an imported package (e.g., writing redis := redis.NewClient()). This shadows the package, making it impossible to access other functions in that package within the same scope.
The Fix: Use unique variable names (e.g., redisClient) or use an import alias to rename the package if you must keep the variable name.

15. Missing code documentation

The Problem: Failing to document exported elements. This forces users to read the implementation logic to understand how to use an API.
The Fix: Every exported element should have a comment starting with its name. Use a doc.go file for package-level documentation. Focus on what the code does and why, rather than how.

16. Not using linters

The Problem: Relying solely on the compiler. The compiler ensures the code runs, but it doesn't catch unidiomatic code, shadowed variables, or common logic pitfalls.
The Fix: Use tools like go vet and golangci-lint. Automate these in your CI/CD pipeline to maintain high code quality and catch mistakes described in this book automatically.

17. Creating confusion with octal literals

The Problem: In Go, an integer starting with a 0 is interpreted as an octal (base 8). For example, 10 + 010 equals 18, not 20. This can lead to very confusing bugs in calculations.
The Fix: To represent octals clearly, use the 0o prefix (e.g., 0o10). This makes the intent explicit and prevents readers from misinterpreting the value as a decimal.

18. Neglecting integer overflows

The Problem: Go does not panic on integer overflows; it silently wraps the value around (e.g., math.MaxInt64 + 1 becomes a large negative number).
The Fix: If you are dealing with critical calculations or user-provided inputs, manually check for overflows using constants like math.MaxInt before performing the operation.

19. Not understanding floating points

The Problem: Floating-point math (float32/float64) is an approximation of real numbers. Comparing two floats with == is dangerous because precision loss can occur during calculations.
The Fix: Compare floats using a "delta" or "epsilon" (checking if the difference is very small). Also, when performing many additions, group numbers of similar magnitudes together to maintain better accuracy.

20. Not understanding slice length and capacity

The Problem: Confusing a slice's len (current elements) with its cap (total space in the backing array). Not realizing that a slice is just a window into a backing array can lead to unintended side effects when multiple slices share the same array.
The Fix: Understand that append might modify the original backing array if there is remaining capacity. Use the "full slice expression" (s[low:high:max]) to limit capacity and prevent sub-slices from accidentally overwriting data in the parent slice.

21. Inefficient slice initialization

The Problem: Initializing a slice with make([]T, 0) and then appending elements inside a loop causes Go to repeatedly reallocate the backing array and copy data as the slice grows.
The Fix: If the final size is known (or can be estimated), initialize the slice with a specific capacity: make([]T, 0, length). This allocates the memory once, drastically improving performance.

22. Being confused about nil vs. empty slices

The Problem: Confusion between a nil slice (var s []int) and an empty slice (s := []int{}). While both have a length of 0, they are handled differently by some libraries (e.g., encoding/json encodes a nil slice as null and an empty slice as []).
The Fix: Use the nil slice by default unless a specific library requires an empty slice. A nil slice is more efficient as it doesn't require an allocation.

23. Not properly checking if a slice is empty

The Problem: Checking for a nil slice (s != nil) to see if it contains elements. If the slice is empty but not nil, the check will pass incorrectly.
The Fix: Always check the length: len(s) == 0. This works accurately for both nil and empty slices.

24. Not making slice copies correctly

The Problem: Forgetting that copy(dst, src) only copies up to the minimum of the two slice lengths. If dst is initialized with length 0 (e.g., var dst []int), copy will move zero elements.
The Fix: Ensure the destination slice is initialized with a length equal to the number of elements you want to copy: dst := make([]int, len(src)).

25. Unexpected side effects using slice append

The Problem: Slicing a slice (s2 := s1[1:2]) creates a new slice that shares the same backing array. If s2 has remaining capacity, calling append on it will modify the original data in s1.
The Fix: Use the "full slice expression" (s1[low:high:max]) to set the capacity of the sub-slice equal to its length, forcing Go to allocate a new array if an append occurs.

26. Slices and memory leaks

The Problem: Creating a tiny sub-slice from a massive backing array keeps the entire array in memory as long as that sub-slice is referenced.
The Fix: If you only need a small part of a large slice, copy the necessary elements into a new slice so the GC can reclaim the large backing array.

27. Inefficient map initialization

The Problem: Maps in Go are hash tables. As they grow, they must re-allocate buckets and re-hash existing keys, which is expensive.
The Fix: Just like slices, if you know the number of elements in advance, initialize the map with a size hint: make(map[K]V, size).

28. Maps and memory leaks

The Problem: Deleting elements from a map does not shrink the number of buckets it has allocated. A map that once held 1 million keys will still consume roughly the same amount of memory after those keys are deleted.
The Fix: If a map’s memory usage is a problem, periodically create a new map and copy the active elements to it, allowing the old, bloated map to be garbage collected.

29. Comparing values incorrectly

The Problem: Using the == operator on types that are not "comparable" (like slices or maps) will cause a compile-time error. Using reflect.DeepEqual is a solution but is very slow due to reflection overhead.
The Fix: For performance-critical code, write a custom equality function. For general cases, understand that reflect.DeepEqual treats nil and empty collections as different, which may not be what you want.

30. Ignoring the fact that elements are copied in range loops

The Problem: In a for _, v := range s loop, the variable v is a copy of the element. Modifying v (e.g., v.Balance = 100) does not update the actual value in the slice s.
The Fix: To modify elements in the collection, access them using the index: s[i].Balance = 100.

31. Ignoring how arguments are evaluated in range loops

The Problem: The expression provided to range (the slice, map, etc.) is evaluated only once at the beginning of the loop. If you append elements to the slice you are iterating over, the loop will not "see" them because it is iterating over a copy of the initial slice header.
The Fix: Use a standard for i := 0; i < len(s); i++ loop if the length of the collection changes during iteration, as len(s) is re-evaluated every step.

32. Ignoring the impact of using pointer elements in range loops

The Problem: In a for _, v := range slice loop, v is a single variable that is updated with the current element’s value in each iteration. If you store the address of v (&v) in a map or slice, every entry will point to the same memory address, which eventually holds the value of the final element.
The Fix: Create a local copy inside the loop (val := v) and take the address of that local variable, or use the index to reference the element directly: &slice[i].

33. Making wrong assumptions during map iterations

The Problem: Maps in Go are intentionally non-deterministic. Iterating over the same map twice will likely yield a different order. Additionally, adding an element during iteration does not guarantee it will be visited; it might be produced later in the loop or skipped entirely.
The Fix: Never rely on map order. If you need to add elements while iterating, store them in a temporary map or slice first and merge them after the loop finishes.

34. Ignoring how the break statement works

The Problem: A break statement inside a switch or select block that is itself inside a for loop will only break out of the switch or select—the loop will continue to the next iteration.
The Fix: Use a label to specify which block you want to break (e.g., break loopLabel).

35. Using defer inside a loop

The Problem: defer functions are not executed when the loop iteration finishes; they execute when the surrounding function returns. In a loop that opens many files or database connections, this can lead to resource exhaustion because nothing is closed until the very end of the function.
The Fix: Move the loop's internal logic into a helper function (where defer will work per-call) or handle the cleanup manually without defer.

36. Not understanding the concept of a rune

The Problem: Confusing bytes with characters. A string in Go is a sequence of bytes. A rune is a Unicode code point. Some characters (like emojis or accented letters) take up multiple bytes (UTF-8). len(str) returns the number of bytes, not characters.
The Fix: Use the unicode/utf8 package (e.g., utf8.RuneCountInString) to accurately count characters.

37. Inaccurate string iteration

The Problem: Iterating over a string with a simple index (s[i]) retrieves the byte at that position. If the string contains multi-byte characters, you will get broken "half-characters."
The Fix: Use a range loop over the string, which automatically yields runes, or convert the string to a []rune slice first.

38. Misusing trim functions

The Problem: Confusing strings.TrimRight with strings.TrimSuffix. TrimRight removes all characters found in the provided "cutset" from the end of the string. For example, TrimRight("123oxo", "xo") results in "123", not "123o".
The Fix: Use TrimSuffix if you want to remove a specific string ending. Use TrimRight only if you want to strip a set of varying characters.

39. Under-optimized string concatenation

The Problem: Because strings are immutable, using the + operator in a loop (e.g., s += str) forces Go to allocate a new string and copy the old data every single time. This results in 𝑂(𝑛2) time complexity.
The Fix: Use strings.Builder. It allocates a buffer that grows efficiently, significantly reducing memory allocations and time.

40. Useless string conversions

The Problem: Converting a []byte to a string (or vice versa) involves a memory allocation and a copy of the data. Doing this frequently—especially in high-performance I/O—can create significant pressure on the Garbage Collector.
The Fix: Check the bytes package. Most operations available in the strings package have a direct equivalent in the bytes package that works on byte slices without needing conversion.

41. Substrings and memory leaks

The Problem: Slicing a string (s2 := s1[0:5]) creates a new string header that points to the same backing array as the original string. If you extract a small substring from a massive string (like a large log file), the entire massive array remains in memory as long as that small substring is alive.
The Fix: Force a copy of the data by converting the substring to a []byte and back to a string: s2 := string([]byte(s1[0:5])), or use strings.Clone(s1[0:5]) in Go 1.18+.

42. Not knowing which type of receiver to use

The Problem: Confusion over whether to use a value receiver (t T) or a pointer receiver (t *T). Choosing incorrectly can lead to bugs (mutating a copy instead of the original) or performance hits.
The Fix: Use a pointer receiver if the method needs to mutate the struct, or if the struct is large or contains non-copyable fields (like sync.Mutex). Use a value receiver if the struct is small, immutable, or a basic type (like int).

43. Never using named result parameters

The Problem: Returning multiple values of the same type (e.g., func GetCoords() (float32, float32, error)) is ambiguous. The caller doesn't know which is the latitude and which is the longitude without reading the documentation.
The Fix: Use named results (lat, lng float32, err error) to self-document the API and improve readability.

44. Unintended side effects with named result parameters

The Problem: Named result parameters are initialized to their zero values. If a function is complex and returns early, it’s easy to return a "shadowed" zero value (like a nil error) even if a problem actually occurred earlier in the function.
The Fix: Be careful with assignment in functions using named parameters. Either explicitly assign the result variables or use them only for simple functions where the return values are obvious.

45. Returning a nil receiver

The Problem: An interface is a wrapper that contains two things: a type and a value. If you return a nil pointer of a specific type (e.g., *MyError(nil)) as an error interface, the interface itself is not nil. A check like if err != nil will evaluate to true, even though the error value is nil.
The Fix: Always return an explicit nil instead of a nil pointer when indicating success: return nil instead of return myNilPointer.

46. Using a filename as a function input

The Problem: Writing functions that accept a string filename limits the function to local files only. It also makes unit testing difficult because you must create real files on disk.
The Fix: Accept an io.Reader (or io.Writer). This makes the function work with files, network sockets, strings, or in-memory buffers, and makes testing trivial with strings.NewReader.

47. Ignoring how defer arguments and receivers are evaluated

The Problem: Arguments passed to a defer function are evaluated immediately at the line where defer is called, not when the function actually executes. This can lead to logging the wrong state or using outdated variables.
The Fix: To use the final state of a variable, use a closure: defer func() { log(currentValue) }(). This ensures the variable is evaluated when the deferred function actually runs.

48. Panicking

The Problem: Using panic for standard error handling (like a missing file or a bad network connection) is unidiomatic and crashes the program unnecessarily.
The Fix: Use panic only for truly unrecoverable errors that represent a programmer's error (like an out-of-bounds index) or a failed mandatory setup in an init() function. For everything else, return an error.

49. Ignoring when to wrap an error

The Problem: Returning a "raw" error up the stack makes it hard to identify where the error happened. Conversely, using fmt.Errorf with %v creates a new string that "swallows" the original error type, making it impossible for the caller to check the error type.
The Fix: Use the %w directive in fmt.Errorf to "wrap" the error. This adds context while allowing the caller to use errors.Is or errors.As to inspect the underlying cause.

50. Checking an error type inaccurately

The Problem: Using direct type assertions (err.(MyError)) or direct comparison (err == ErrSentinel) fails if the error has been wrapped.
The Fix: Since Go 1.13, always use errors.As(err, &target) to check for an error type and errors.Is(err, ErrSentinel) to check for a specific error value. These functions correctly navigate the "wrapped" error chain.

51. Checking an error value inaccurately

The Problem: Comparing an error to a sentinel value using the == operator (e.g., if err == sql.ErrNoRows) fails if the error has been wrapped with fmt.Errorf and %w.
The Fix: Use errors.Is(err, target). This function recursively unwraps the error to see if any error in the chain matches the target sentinel value.

52. Handling an error twice

The Problem: Both logging an error and returning it up the stack. This leads to "log pollution" where a single failure results in multiple confusing log entries at different levels of the application.
The Fix: An error should be handled only once. Either log the error (and usually stop the flow) OR return it with added context (wrapping) so the caller can handle it.

53. Not handling an error

The Problem: Calling a function that returns an error but ignoring it entirely (e.g., f()). This leaves the program in an unpredictable state if the operation fails, and it hides intent from future readers.
The Fix: If you must ignore an error, do it explicitly using the blank identifier: _ = f(). This signals to others that the neglect was intentional.

54. Not handling defer errors

The Problem: Writing defer r.Close() without checking the error it returns. Closing a file or a database connection can fail (e.g., failing to flush a buffer to disk), and ignoring this failure can lead to silent data loss.
The Fix: Use a closure in the defer statement and handle the error by logging it or using named return parameters to propagate the error to the caller.

55. Mixing up concurrency and parallelism

The Problem: Thinking they are the same thing. This confusion leads to poor architectural choices when designing high-performance systems.
The Fix: Understand the difference: Concurrency is about structure (dealing with many things at once by breaking them into independent pieces); Parallelism is about execution (doing many things at the same time using multiple CPU cores).

56. Thinking concurrency is always faster

The Problem: Assuming that wrapping a task in a goroutine will automatically make it faster. Goroutines have overhead (creation, scheduling, and context switching), and synchronization (mutexes/channels) adds latency.
The Fix: For small, fast tasks, sequential execution is often faster. Always benchmark your concurrent code to ensure the overhead is justified by the performance gains.

57. Being puzzled about when to use channels or mutexes

The Problem: Attempting to force channels into every situation because "Go uses channels." This can lead to overly complex and less efficient code.
The Fix: Use mutexes for protecting shared state (internal data structures). Use channels for orchestration, signaling, or transferring ownership of data between different parts of the system.

58. Not understanding race problems

The Problem: Confusing a data race with a race condition. A data race is two goroutines accessing the same memory concurrently with one being a write. A race condition is an error where the application's behavior depends on the uncontrolled timing of events.
The Fix: Use the -race detector to catch data races. Fix race conditions through proper synchronization and coordination, ensuring that logic doesn't depend on which goroutine "wins" a race.

59. Not understanding the concurrency impacts of a workload type

The Problem: Treating CPU-bound and I/O-bound workloads the same. For example, spinning up 10,000 goroutines for a CPU-intensive task on an 8-core machine will cause massive performance degradation due to thrashing.
The Fix: For CPU-bound tasks, limit the number of goroutines to the number of available cores (GOMAXPROCS). For I/O-bound tasks (like network calls), you can use many more goroutines to keep the CPU busy while others are waiting.

60. Misunderstanding Go contexts

The Problem: Using context.Context as a "bag" to pass optional parameters or not understanding how cancellation propagates.
The Fix: Use context for two main things: Cancellation/Deadlines (signaling a process to stop) and Metadata (request-scoped values like Trace IDs). Always call the cancel function returned by WithCancel or WithTimeout to avoid resource leaks.

61. Propagating an inappropriate context

The Problem: Passing a context attached to an HTTP request to an asynchronous task (like a background Kafka publication). Once the HTTP handler returns the response, the original context is automatically canceled, causing the background task to fail unexpectedly.
The Fix: If a background task must outlive the request, create a custom context that "detaches" the cancellation signal from the parent while still carrying the parent’s values (e.g., Trace IDs).

62. Starting a goroutine without knowing when to stop it

The Problem: Creating "orphan" goroutines that have no clear exit point. This leads to goroutine leaks, where memory and resources (like open files or network connections) are never reclaimed.
The Fix: Whenever you start a goroutine, define exactly how it will stop. Use a context.Context to signal cancellation or a dedicated "quit" channel, and ensure the parent waits for the child to finish if the application is shutting down.

63. Not being careful with goroutines and loop variables

The Problem: Using a loop variable inside a goroutine closure (e.g., for _, i := range s { go func() { print(i) }() }). Because the goroutines share the same memory address for the loop variable, they will likely all print the final value of the loop.
The Fix: Create a local variable inside the loop (val := i) to capture the current value, or pass the variable as an argument to the goroutine's anonymous function.

64. Expecting deterministic behavior using select and channels

The Problem: Assuming that select will prioritize cases in the order they are written. In reality, if multiple channels are ready at the same time, Go picks one randomly to prevent starvation.
The Fix: If prioritization is required (e.g., processing messages before a disconnection signal), use a nested select with a default case to "drain" the high-priority channel before exiting.

65. Not using notification channels

The Problem: Using chan bool or chan int to signal that "something happened." This can be confusing because the receiver might expect the data (the true or 1) to have actual meaning.
The Free Fix: Use chan struct{} for signaling. An empty struct (struct{}) occupies zero bytes and clearly communicates that the message's content is irrelevant—only the occurrence of the event matters.

66. Not using nil channels

The Problem: Dealing with closed channels in a select block. Receiving from a closed channel returns immediately with a zero value. In a loop, this causes the select to spin infinitely on the closed case, wasting CPU.
The Fix: Once you detect a channel is closed, set its variable to nil. A select statement will never choose a nil channel, effectively disabling that case and allowing the loop to continue with the remaining channels.

67. Being puzzled about channel size

The Problem: Choosing arbitrary buffer sizes (like make(chan int, 40)) or misunderstanding the difference between unbuffered and buffered channels. Unbuffered channels provide synchronization; buffered channels do not.
The Fix: Default to unbuffered channels. Use a buffer of 1 for simple asynchronous signaling. Use larger buffers only for specific patterns (like worker pools) where you have benchmarked the performance benefit.

68. Forgetting about possible side effects with string formatting

The Problem: Using fmt.Sprintf or logging an object within a critical section. If that object has a String() method that also tries to acquire a mutex, it can cause a deadlock or a data race (if the object is being mutated elsewhere).
The Fix: Be careful when formatting objects in concurrent code. Narrow the scope of your mutexes or avoid passing objects that implement fmt.Stringer into logs while a lock is held.

69. Creating data races with append

The Problem: Assuming append is thread-safe. If two goroutines append to the same slice that has remaining capacity, they will both write to the same index in the backing array, causing a data race.
The Fix: Treat slices as shared state that must be protected by a mutex, or ensure that each goroutine works on its own local copy of the slice.

70. Using mutexes inaccurately with slices and maps

The Problem: Performing a "shallow" copy of a map or slice within a mutex (e.g., m2 := m1). Since maps and slices are headers containing pointers to the underlying data, the "copy" still points to the same memory. Accessing m2 outside the lock is still a data race.
The Fix: To safely access shared data outside a lock, you must perform a deep copy (iterate through the collection and copy each element to a new instance) while the mutex is held.

71. Misusing sync.WaitGroup

The Problem: Calling wg.Add(1) inside the child goroutine rather than in the parent. Because goroutine execution is non-deterministic, the parent might reach wg.Wait() before the child starts and calls Add, causing the program to finish before the work is done.
The Fix: Always call wg.Add() in the parent goroutine before the go statement that launches the worker.

72. Forgetting about sync.Cond

The Problem: Using busy-waiting loops (repeatedly checking a variable) or complex channel logic to notify multiple goroutines about a shared state change.
The Fix: Use sync.Cond. It provides a "rendezvous point" for goroutines. It allows one goroutine to Broadcast() a signal to all waiting goroutines once a specific condition (like a donation goal being reached) is met, which is much more CPU-efficient than a loop.

73. Not using errgroup

The Problem: Manually managing sync.WaitGroup along with error channels and context cancellation when running parallel tasks.
The Fix: Use the golang.org/x/sync/errgroup package. It simplifies spawning subtasks, captures the first error that occurs, and can automatically cancel a shared context to stop other tasks if one fails.

74. Copying a sync type

The Problem: Passing a sync.Mutex, sync.WaitGroup, or sync.Cond by value (e.g., using a value receiver func (c Counter) Inc()). This copies the internal state of the sync primitive, meaning the copy and the original are not synchronized, leading to data races.
The Fix: Never copy sync types. Always pass them by pointer or use a pointer receiver for methods that contain them.

75. Providing a wrong time duration

The Problem: Passing a raw integer to a function expecting a time.Duration (e.g., time.NewTicker(1000)). Since the base unit for time.Duration is one nanosecond, this creates a ticker for one microsecond, not one second.
The Fix: Always use the time constants provided by the time package (e.g., time.NewTicker(1000 * time.Millisecond) or time.Second).

76. time.After and memory leaks

The Problem: Using time.After(duration) inside a loop (usually in a select statement). time.After creates a new timer that is only reclaimed by the Garbage Collector once it expires. If the loop runs frequently and another select case is usually chosen, thousands of timers can accumulate.
The Fix: Use time.NewTimer instead. Create it once before the loop and call Reset() on it at the start of each iteration.

77. Common JSON-handling mistakes

The Problem: Three common pitfalls: (1) Type Embedding: Embedding time.Time in a struct makes the whole struct inherit time.Time’s custom JSON marshaler. (2) Monotonic Clocks: Comparing a time.Time before and after marshaling fails because JSON doesn't store the monotonic part of the clock. (3) Map of any: Numbers in map[string]any are always unmarshaled as float64.
The Fix: Use named fields for time.Time, use t.Equal() for time comparisons, and be mindful of type assertions when reading numbers from generic maps.

78. Common SQL mistakes

The Problem: (1) Forgetting that sql.Open only validates arguments, it doesn't verify a connection (use Ping). (2) Using the default connection pool limits (unlimited connections). (3) Not using prepared statements for repeated queries. (4) Not checking rows.Err() after a loop.
The Fix: Call db.Ping() after opening, tune SetMaxOpenConns, use db.Prepare(), and always check the error status of a row iterator.

79. Not closing transient resources

The Problem: Forgetting to close resp.Body (HTTP), sql.Rows, or os.File. This leads to resource leaks (file descriptors) and can prevent the reuse of TCP connections.
The Fix: Use defer r.Close() immediately after checking that the resource was opened without error. For HTTP clients, you must also drain the body (io.Copy(io.Discard, resp.Body)) to ensure the connection returns to the pool.

80. Forgetting the return statement after replying to an HTTP request

The Problem: Calling http.Error(w, ...) but not exiting the function. The handler will continue to execute, potentially trying to write more headers or data, which leads to "superfluous response.WriteHeader call" errors.
The Fix: Always follow an error response with a return statement.

81. Using the default HTTP client and server

The Problem: Default http.Client and http.Server implementations have no timeouts. This can lead to stuck goroutines, resource exhaustion, and vulnerability to "Slowloris" attacks. Additionally, the default client only allows 2 idle connections per host, severely limiting performance for high-traffic services.
The Fix: Always define a custom http.Client with explicit Timeout and Transport settings. On the server side, use http.TimeoutHandler and set ReadHeaderTimeout to ensure connections are closed if the client is too slow.

82. Not categorizing tests

The Problem: Running fast unit tests alongside slow integration tests or those requiring external dependencies (like databases) makes the development cycle slow and discourages frequent testing.
The Fix: Use build tags (e.g., //go:build integration) to separate test types. You can also use testing.Short() to skip long-running tests or use environment variables to enable specific test suites.

83. Not enabling the -race flag

The Problem: Data races are one of the most common and difficult-to-debug issues in concurrent Go programs. Many developers forget to enable the race detector during testing.
The Fix: Always run your tests with the -race flag in your CI/CD pipeline and during local development. While it adds overhead, catching a data race before production is worth the performance cost.

84. Not using test execution modes

The Problem: Running tests sequentially when they could be parallelized, or failing to identify hidden dependencies between tests that only surface when executed in a specific order.
The Fix: Use t.Parallel() to speed up test execution. Use the -shuffle flag (Go 1.17+) to randomize the execution order; this helps find "brittle" tests that pass only because of the state left behind by a previous test.

85. Not using table-driven tests

The Problem: Writing a separate test function for every possible input/output combination leads to massive code duplication and makes it harder to add new test cases or update logic.
The Free Fix: Use table-driven tests. Define a slice or map of structs containing inputs and expected outputs, then use a single loop with t.Run() to execute subtests.

86. Sleeping in unit tests

The Problem: Using time.Sleep() to wait for an asynchronous operation to finish. This makes tests slow and "flaky" (they might fail if the machine is under load).
The Fix: Use synchronization (like channels or sync.WaitGroup) or a retry mechanism. Periodically poll for the expected condition to be met rather than waiting a fixed, arbitrary amount of time.

87. Not dealing with the time API efficiently

The Problem: Functions that call time.Now() directly are impossible to test with specific timestamps, leading to non-deterministic test results.
The Fix: Use dependency injection for time. Pass a "clock" function or interface into your struct, or simply pass the specific time.Time required as an argument to the function.

88. Not using testing utility packages

The Problem: Manually implementing mocks for HTTP requests or trying to simulate complex I/O failures.
The Fix: Use the standard library's utility packages. Use net/http/httptest to record responses or spin up mock servers. Use testing/iotest to simulate readers that return data in chunks or fail with timeouts.

89. Writing inaccurate benchmarks

The Problem: Including expensive setup time in the benchmark results, or writing benchmarks that are so simple the compiler "inlines" or optimizes them away entirely.
The Fix: Call b.ResetTimer() after setup. To prevent compiler optimizations from deleting your code, assign the result of the function under test to a global variable so the compiler believes the result is actually needed.

90. Not exploring all the Go testing features

The Problem: Missing out on advanced features like code coverage, black-box testing, or clean teardown logic.
The Fix: Use -coverprofile to find untested code paths. Use the _test suffix for your test package (e.g., package stringutils_test) to ensure you are only testing the public API. Use t.Cleanup() for a more robust alternative to defer for resource teardown.

Continuing with the final summary of mistakes 91 through 100 from 100 Go Mistakes and How to Avoid Them. This final section focuses heavily on Optimizations and "mechanical sympathy" (understanding how the underlying hardware and runtime work).

91. Not understanding CPU caches

The Problem: CPUs fetch memory in 64-byte "cache lines," not individual words. If your data is scattered across memory (e.g., a slice of pointers to small objects), the CPU will constantly miss the cache and fetch from the much slower RAM.
The Fix: Favor "spatial locality." Organize data contiguously. Use slices of values instead of slices of pointers when performance is critical, so that one cache line fetch brings in multiple elements.

92. Writing concurrent code that leads to false sharing

The Problem: Two goroutines on different cores update two independent variables that happen to reside on the same 64-byte cache line. Every time one core writes, it invalidates the cache for the other core, forcing it to reload from RAM. This can make concurrent code slower than sequential code.
The Fix: Use "padding." Add empty fields (e.g., _ [56]byte) between struct fields that are updated frequently by different goroutines to ensure they sit on separate cache lines.

93. Not taking into account instruction-level parallelism (ILP)

The Problem: Modern CPUs execute multiple instructions in parallel if they don't depend on each other. "Data hazards" occur when one line of code needs the result of the previous one, forcing the CPU to execute them sequentially.
The Fix: Rework performance-critical loops to reduce dependencies. Sometimes, introducing a temporary variable or unrolling a loop slightly can break a dependency chain, allowing the CPU to parallelize the instructions.

94. Not being aware of data alignment

The Problem: Go aligns fields in a struct based on their size. If you order fields poorly (e.g., byte, int64, byte), Go adds "padding" bytes to ensure the int64 is aligned, making the struct much larger in memory than necessary.
The Fix: Order struct fields in descending order (largest types first). This minimizes padding and reduces the overall memory footprint, allowing more objects to fit in the CPU cache.

95. Not understanding stack vs. heap

The Problem: Variables on the stack are "self-cleaning" and fast; variables on the heap must be managed by the Garbage Collector (GC), which consumes CPU. Many developers use pointers unnecessarily, "escaping" variables to the heap.
The Fix: Understand "escape analysis." Rule of thumb: "Sharing up" (returning a pointer to a local variable) escapes to the heap. "Sharing down" (passing a pointer into a function) usually stays on the stack. Avoid pointers for small, short-lived variables.

96. Not knowing how to reduce allocations

The Problem: Frequent allocations in a hot path (like a loop or high-frequency handler) create massive pressure on the GC, leading to "Stop the World" pauses and high CPU usage.
The Fix: Use sync.Pool to reuse temporary objects (like buffers). Design APIs to be "allocation-friendly"—for example, let the caller provide a buffer (like io.Reader.Read) so they can reuse the same memory for multiple calls.

97. Not relying on inlining

The Problem: Every function call has a small overhead. The Go compiler automatically "inlines" simple functions (replaces the call with the code), but it has an "inlining budget." If a function is too complex, it won't be inlined.
The Fix: Keep the "fast path" of your functions simple. If you have complex error handling or logic, move it into a separate "slow path" helper function. This keeps the main function small enough for the compiler to inline.

98. Not using Go diagnostics tooling

The Problem: Attempting to optimize code based on "gut feelings" or intuition rather than data.
The Fix: Master the three main tools: (1) pprof for CPU and memory profiling. (2) The Execution Tracer to see goroutine scheduling and GC behavior. (3) GC Traces (GODEBUG=gctrace=1) to monitor how often the garbage collector runs and how much memory it frees.

99. Not understanding how the GC works

The Problem: Being unaware that the GC is "concurrent" but still has "stop-the-world" phases. Not knowing that the GOGC variable controls the trade-off between CPU usage and memory pressure.
The Fix: Tune the GOGC environment variable. Increasing it (e.g., GOGC=200) makes the GC run less often (saving CPU) at the cost of using more memory. For high-traffic applications, consider the "ballast" trick (allocating a large unused slice) to reduce GC frequency.

100. Impacts of running Go in Docker and Kubernetes

The Problem: Go’s runtime determines GOMAXPROCS based on the host's CPU count, not the Kubernetes CPU limit. If you have a 4-core limit on a 64-core host, Go will still try to use 64 threads. This leads to the process being "throttled" by the Linux CFS (Completely Fair Scheduler), causing massive latency spikes.
The Fix: Use the uber-go/automaxprocs library. By importing it once in your main.go, it will automatically set GOMAXPROCS to match the Linux container CPU quota, preventing throttling.