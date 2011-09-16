@interface bad : NSViewController {
    __strong BOOL state;
    __strong NSArray *foo2;
    __weak NSError *error;
    __weak NSString *testWeak;
    __autoreleasing int specialCopy;
}

@property (nonatomic, readonly, strong) __block int lineNum;
@property (atomic, copy) NSMutableString *temp;
@property (strong) __block NSArray *foo; //!lint-ignore
@property (nonatomic, weak) IBOutlet UITextField *text;
@property (unsafe_unretained) UIColor *crapColor;
@property (unsafe_unretained) UIColor *crapColorUnsafe;
@end