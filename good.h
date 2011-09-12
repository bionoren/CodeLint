@interface bad : NSViewController {
    BOOL state;
    NSArray *foo2;
    __weak NSError* error;
    __weak testWeak;
    __autoreleasing specialCopy;
}

@property (nonatomic, readonly, strong) __block int lineNum;
@property (atomic, strong) NSMutableString *temp;
@property (atomic, copy) __block NSArray *foo;
@property (nonatomic, strong) IBOutlet UITextField *text;
@property (atomic, strong) UIColor *crapColor;
@property (atomic, unsafe_unretained) UIColor *crapColorUnsafe;
@end